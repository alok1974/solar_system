import random
from pathlib import Path

import numpy as np
from PIL import Image


# Define 3D vector operations
def add(v0, v1):
    return [v0[i]+v1[i] for i in range(3)]


def sub(v0, v1):
    return [v0[i]-v1[i] for i in range(3)]


def dot(v0, v1):
    return sum([v0[i]*v1[i] for i in range(3)])


def length(v):
    return np.sqrt(dot(v, v))


def normalize(v):
    v_len = length(v)
    return [v[i]/v_len for i in range(3)] if v_len != 0 else [0]*3


def _get_random_sphere(cons_color=None, center=None, radius_min=None, radius_max=None):
    if center is None:
        center = [
            random.randint(-10, 10),
            random.randint(-10, 10),
            5,
        ]

    r_min = radius_min or 1
    r_max = radius_max or 3
    radius = random_range(r_min, r_max)

    if cons_color is not None:
        color = cons_color
    else:
        color = [
            random.randint(50, 255),
            random.randint(50, 255),
            random.randint(100, 255),
        ]

    return (center, radius, color, False, True), (1, 1, 1, 0, 0)


def random_range(a, b):
    return a + (b - a) * random.random()


def get_sphere_pixel_color(camera, ray_dir, lights, sphere_light_data):
    sphere, light_linking = sphere_light_data
    center, radius, color, constant_color, randomize_color = sphere

    intersection, normal = compute_intersection(camera, ray_dir, center, radius)

    if intersection is None or normal is None:
        return None

    if randomize_color:
        color = get_randomized_color(color)

    diffuse = 0
    for (l_pos, l_int), link in zip(lights, light_linking):
        if not link:
            continue

        if l_int == 0:
            continue

        # Compute lighting
        to_light = normalize(sub(l_pos, intersection))
        if constant_color:
            diffuse = 1
        else:
            diffuse = (max(0, dot(normal, to_light)) * l_int) + diffuse

    # Set pixel color
    return tuple([int(diffuse * color[i]) for i in range(3)])


def compute_discriminant(camera, ray_dir, center, radius):
    oc = sub(camera, center)
    a = dot(ray_dir, ray_dir)
    b = 2 * dot(oc, ray_dir)
    c = dot(oc, oc) - radius * radius

    discriminant = b * b - 4 * a * c
    if discriminant < 0:
        return None, None

    t = (-b - np.sqrt(discriminant)) / (2 * a)
    if t < 0:
        return None, None

    return discriminant, t


def compute_intersection(camera, ray_dir, center, radius):
    discriminant, t = compute_discriminant(camera, ray_dir, center, radius)
    if discriminant is None or t is None:
        return None, None

    # Compute intersection point and normal
    intersection = add(camera, [t * ray_dir[i] for i in range(3)])
    normal = normalize(sub(intersection, center))

    return intersection, normal


def get_randomized_color(color):
    return (
        color[0] * random_range(0.7, 1.0),
        color[1] * random_range(0.7, 1.0),
        color[2] * random_range(0.7, 1.0),
    )


def render_comets(x, y, comet, ray_dir, pixels):
    if y % 27 == 0:
        pixel_color = get_sphere_pixel_color(
            camera=camera,
            ray_dir=ray_dir,
            lights=lights,
            sphere_light_data=comet,
        )
        if pixel_color is not None:
            pixels[x, y] = pixel_color


def render_stars(x, y, ray_dir, pixels):
    star = _get_random_sphere()
    pixel_color = get_sphere_pixel_color(
        camera=camera,
        ray_dir=ray_dir,
        lights=lights,
        sphere_light_data=star,
    )
    if pixel_color is not None:
        pixels[x, y] = pixel_color


def render_solar_winds(x, y, aspect, height, pixels):
    # Generate random star data
    star_x = -0.9
    star_y = 0
    star_radius = random_range(0.2, 0.6) * aspect * height

    star_color = (
        random.randint(200, 255),
        random.randint(150, 165),
        random.randint(10, 30),
    )

    render_circular_stars(x, y, star_x, star_y, star_radius, star_color, aspect, height, pixels)


def render_circular_stars(x, y, star_x, star_y, star_radius, star_color, aspect, height, pixels):
    # Convert 3D world coordinates to 2D pixel coordinates
    star_px = (star_x / fov / aspect + 1) * width / 2
    star_py = (1 - star_y / fov) * height / 2

    # Compute the distance from the pixel to the star
    dist = np.sqrt((x - star_px) ** 2 + (y - star_py) ** 2)

    # If the pixel is within the star's radius, return the star's color
    if dist <= star_radius:
        pixels[x, y] = star_color


def render_planet(x, y, planet, ray_dir, pixels):
    pixel_color = get_sphere_pixel_color(
        camera=camera,
        ray_dir=ray_dir,
        lights=lights,
        sphere_light_data=planet,
    )
    if pixel_color is not None:
        pixels[x, y] = pixel_color


def render(width, aspect, fov, output_file_path):
    height = int(width / aspect)
    image = Image.new("RGB", (width, height), (18, 8, 12))
    pixels = image.load()

    for y in range(height):
        print(f'{y}/{height}')
        curr_y = (1 - 2 * (y + 0.5) / height) * fov
        comet = _get_random_sphere(
            center=[
                random_range(-3, 3),
                random_range(curr_y - 2, curr_y + 2),
                5,
            ],
            radius_min=0.1,
            radius_max=1.0,
        )

        for x in range(width):
            px = (2 * (x + 0.5) / width - 1) * aspect * fov
            py = (1 - 2 * (y + 0.5) / height) * fov
            pixel_pos = [px, py, 0]

            # Compute ray direction
            ray_dir = normalize(sub(pixel_pos, camera))

            # BG Stars
            render_stars(x, y, ray_dir, pixels)

            # Comets
            render_comets(x, y, comet, ray_dir, pixels)

            # Glowing Stars
            for glowing_star in glowing_stars:
                (star_x, star_y), star_radius, star_color = glowing_star
                render_circular_stars(x, y, star_x, star_y, star_radius, star_color, aspect, height, pixels)

            # Solar system
            for planet in solar_system:
                render_planet(x, y, planet, ray_dir, pixels)

            # Solar winds
            render_solar_winds(x, y, aspect, height, pixels)

    # Save image
    image.save(output_file_path)


# Define scene
camera = [0, 0, -1]  # camera position

# Lighting Data -> (light position, intensity)
sun_light = ([-50, 0, 0], 3)
fill = ([40, -30, -30], 0.20)
rim = ([50, 30, 20], 0.4)
sun_only_illum_top = ([50, 350, 5], 4)
sun_only_illum_bottom = ([50, -260, 5], 1.9)
lights = [sun_light, fill, rim, sun_only_illum_top, sun_only_illum_bottom]


# Sphere Data -> (center, radius, color, is_constant, randomize_color)
sun = ([-6.7, 0, 5], 4, (255, 155, 0), False, True)
mercury = ([-1.9 - 0.37, 0, 5], 0.07, (169, 169, 169), False, False)
venus = ([-1.57 - 0.37, 0, 5], 0.14, (225, 225, 224), False, True)
earth = ([-1.17 - 0.37, 0, 5], 0.15, (0, 128, 255), False, True)
mars = ([-0.84 - 0.37, 0, 5], 0.076, (204, 102, 0), False, False)
jupiter = ([-0.06 - 0.37, 0, 5], 0.60, (189, 183, 107), False, True)
saturn = ([1.18 - 0.37, 0, 5], 0.54, (238, 221, 130), False, True)
uranus = ([2.1 - 0.37, 0, 5], 0.3, (173, 216, 230), False, True)
neptune = ([2.72 - 0.37, 0, 5], 0.22, (70, 130, 180), False, True)


# Solar system -> planet data, light linking information
solar_system = [
    (sun, (1, 1, 1, 1, 1)),
    (mercury, (1, 1, 1, 0, 0)),
    (venus, (1, 1, 1, 0, 0)),
    (earth, (1, 1, 1, 0, 0)),
    (mars, (1, 1, 1, 0, 0)),
    (jupiter, (1, 1, 1, 0, 0)),
    (saturn, (1, 1, 1, 0, 0)),
    (uranus, (1, 1, 1, 0, 0)),
    (neptune, (1, 1, 1, 0, 0)),
]


glowing_stars = [
    (
        # star_x, star_y
        (
            random_range(-0.5, 0.5),
            random_range(-0.5, 0.5),
        ),
        # star radius
        random_range(0.6, 3),
        # star color
        (
            random.randint(200, 255),
            random.randint(200, 255),
            random.randint(200, 255),
        )
    )
    for _ in range(10)
]


width = 1920
aspect = 1.91
fov = .26

output_file_path = str(Path(Path(__file__).parent.parent, 'image', 'render.png'))

render(
    width=width,
    aspect=aspect,
    fov=fov,
    output_file_path=output_file_path,
)
