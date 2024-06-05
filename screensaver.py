import pygame
import sys
import random
import json
import os
from tkinter import messagebox
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import win32api

# Generate JSON configuration file with default settings if it doesn't exist
def generate_config():
    default_settings = {
        "logo_image_path": "logo.png",
        "background_image_path": "background.png",
        "speed": 2
    }
    if not os.path.exists("screensaver_config.json"):
        with open("screensaver_config.json", "w") as f:
            json.dump(default_settings, f, indent=4)
        return True
    return False

# Check if config file was generated
config_generated = generate_config()

# Load settings from JSON configuration file
def load_settings():
    with open("screensaver_config.json", "r") as f:
        settings = json.load(f)
    return settings

# Load settings if config file was generated
if config_generated:
    settings = load_settings()
    messagebox.showinfo("Configuration File Generated", "A configuration file has been generated successfully.")
    exit()

pygame.init()

# Attempt to enable V-Sync
pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, 1)

# Set up fullscreen mode
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.OPENGL)
WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption("DVD Screensaver")
settings = load_settings()
try:
    # Load settings from JSON configuration file
    settings = load_settings()

    # Load background image
    background_image = pygame.image.load(settings["background_image_path"])

    # Load logo image
    logo_image = pygame.image.load(settings["logo_image_path"]).convert_alpha()

    # Load speed value
    default_speed = settings["speed"]

except KeyError as e:
    messagebox.showerror("Configuration Error", f"Key Error: Missing key {e}. Regenerating configuration file.")
    generate_config()
    try:
        settings = load_settings()
        background_image = pygame.image.load(settings["background_image_path"])
        logo_image = pygame.image.load(settings["logo_image_path"]).convert_alpha()
        default_speed = settings["speed"]
    except FileNotFoundError as e:
        if str(e) == settings["background_image_path"] or str(e) == settings["logo_image_path"]:
            messagebox.showerror("File Not Found", f"Image file '{e}' not found.")
        else:
            messagebox.showerror("Configuration Error", "Failed to load settings. Configuration file is missing.")
        pygame.quit()
        sys.exit()
    except Exception as e:
        messagebox.showerror("Configuration Error", f"Failed to load settings: {e}")
        pygame.quit()
        sys.exit()
except FileNotFoundError as e:
    messagebox.showerror("Configuration Error", "Failed to load settings. Configuration file is missing.")
    pygame.quit()
    sys.exit()
except Exception as e:
    messagebox.showerror("Configuration Error", f"Failed to load settings: {e}")
    pygame.quit()
    sys.exit()


logo_rect = logo_image.get_rect()

# Center the logo initially
logo_rect.centerx = WIDTH // 2
logo_rect.centery = HEIGHT // 2

# Calculate speed based on screen size
max_variance = 0.5
speed_scale = min(WIDTH / 800, HEIGHT / 600)
start_logo_speed = default_speed * speed_scale
logo_speed_x = start_logo_speed
logo_speed_y = start_logo_speed
logo_direction = [1, 1]  # Initial direction (x, y)

# Set up OpenGL
glMatrixMode(GL_PROJECTION)
glLoadIdentity()
gluOrtho2D(0, WIDTH, HEIGHT, 0)  # Set orthographic projection
glMatrixMode(GL_MODELVIEW)
glLoadIdentity()

# Enable blending for transparency
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

# Convert Pygame surface to OpenGL texture
def surface_to_texture(surface):
    texture_data = pygame.image.tostring(surface, "RGBA", 1)
    width, height = surface.get_size()
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
    return texture_id

background_texture = surface_to_texture(background_image)
logo_texture = surface_to_texture(logo_image)

# Get the refresh rate of the screen using win32api
def get_refresh_rate():
    device = win32api.EnumDisplayDevices()
    settings = win32api.EnumDisplaySettings(device.DeviceName, -1)
    return settings.DisplayFrequency

refresh_rate = get_refresh_rate()

# Function to add random velocity variance
def add_velocity_variance(speed, start_speed, max_variance):
    new_speed = speed
    while new_speed == speed:  # Ensure new_speed is different
        variance = random.uniform(-max_variance, max_variance)
        new_speed = start_speed + variance
        new_speed = max(start_speed - max_variance, min(start_speed + max_variance, new_speed))
    return new_speed

# Main loop
clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    dt = clock.tick(refresh_rate) / 1000.0  # Amount of time since last frame in seconds

    # Update logo position
    logo_rect.x += logo_speed_x * logo_direction[0] * dt * refresh_rate
    logo_rect.y += logo_speed_y * logo_direction[1] * dt * refresh_rate

    # Bounce off screen edges
    if logo_rect.left < 0 or logo_rect.right > WIDTH:
        logo_direction[0] *= -1
        logo_speed_x = add_velocity_variance(logo_speed_x, start_logo_speed, max_variance)
        logo_rect.x = max(0, min(WIDTH - logo_rect.width, logo_rect.x))  # Prevent sticking
    if logo_rect.top < 0 or logo_rect.bottom > HEIGHT:
        logo_direction[1] *= -1
        logo_speed_y = add_velocity_variance(logo_speed_y, start_logo_speed, max_variance)
        logo_rect.y = max(0, min(HEIGHT - logo_rect.height, logo_rect.y))  # Prevent sticking

    # Draw background and scaled logo using OpenGL
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_TEXTURE_2D)

    # Draw background
    glBindTexture(GL_TEXTURE_2D, background_texture)
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex2f(0, 0)
    glTexCoord2f(1, 0)
    glVertex2f(WIDTH, 0)
    glTexCoord2f(1, 1)
    glVertex2f(WIDTH, HEIGHT)
    glTexCoord2f(0, 1)
    glVertex2f(0, HEIGHT)
    glEnd()

    # Draw logo
    glBindTexture(GL_TEXTURE_2D, logo_texture)
    glBegin(GL_QUADS)
    glTexCoord2f(0, 1)
    glVertex2f(logo_rect.x, logo_rect.y)
    glTexCoord2f(1, 1)
    glVertex2f(logo_rect.x + logo_rect.width, logo_rect.y)
    glTexCoord2f(1, 0)
    glVertex2f(logo_rect.x + logo_rect.width, logo_rect.y + logo_rect.height)
    glTexCoord2f(0, 0)
    glVertex2f(logo_rect.x, logo_rect.y + logo_rect.height)
    glEnd()

    pygame.display.flip()
