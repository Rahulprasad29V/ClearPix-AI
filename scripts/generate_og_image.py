import os
from PIL import Image, ImageDraw, ImageFont

def generate_og_image():
    width = 1200
    height = 630
    img = Image.new("RGBA", (width, height), (15, 16, 14, 255))
    draw = ImageDraw.Draw(img)

    # Subtle radial / gradient background glow in top-right
    for r in range(350, 0, -2):
        alpha = int(24 * (1 - r / 350))
        draw.ellipse([900 - r, 120 - r, 900 + r, 120 + r], fill=(187, 244, 68, alpha))

    # Outer border
    draw.rectangle([20, 20, width - 20, height - 20], outline=(45, 48, 42, 255), width=2)
    
    # Inner subtle lime border corner accents
    draw.line([(30, 30), (70, 30)], fill=(187, 244, 68, 255), width=3)
    draw.line([(30, 30), (30, 70)], fill=(187, 244, 68, 255), width=3)

    # Load system fonts or fallback
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 60)
        font_sub = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 28)
        font_badge = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 20)
        font_author = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 26)
        font_role = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 22)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = font_title
        font_badge = font_title
        font_author = font_title
        font_role = font_title

    # Top Badge: CROSS-PLATFORM AI ENHANCEMENT
    badge_text = "CROSS-PLATFORM AI ENHANCEMENT · REAL-ESRGAN"
    draw.rounded_rectangle([70, 80, 580, 118], radius=6, fill=(28, 30, 25, 255), outline=(50, 55, 45, 255))
    draw.text((90, 89), badge_text, font=font_badge, fill=(187, 244, 68, 255))

    # Main Heading
    draw.text((70, 160), "ClearPix.", font=font_title, fill=(244, 245, 240, 255))
    draw.text((310, 160), "AI Photo Enhancer", font=font_title, fill=(187, 244, 68, 255))

    # Subtitle
    draw.text(
        (70, 250),
        "Enhance photos on any device with AI-powered Real-ESRGAN upscaling.\nWorks across Android, iPhone, Windows, and macOS browsers.",
        font=font_sub,
        fill=(165, 170, 160, 255),
        spacing=10
    )

    # Divider line
    draw.line([(70, 380), (1130, 380)], fill=(40, 44, 38, 255), width=1)

    # Bottom Author & Team Badge Card
    draw.rounded_rectangle([70, 420, 1130, 550], radius=12, fill=(24, 26, 22, 255), outline=(50, 55, 45, 255))
    
    # Initials avatar
    draw.rounded_rectangle([95, 442, 175, 522], radius=10, fill=(35, 40, 30, 255), outline=(187, 244, 68, 120))
    draw.text((115, 465), "RV", font=font_author, fill=(187, 244, 68, 255))

    # Creator Name & Role
    draw.text((195, 450), "Rahulprasad Veeramani", font=font_author, fill=(244, 245, 240, 255))
    draw.text((195, 490), "Branch Head (India) @ CyberWolf Team  ·  https://www.cyberwolf360.in/", font=font_role, fill=(187, 244, 68, 255))

    output_path = "static/og-preview.png"
    img.convert("RGB").save(output_path, "PNG", optimize=True)
    print(f"Generated {output_path} successfully ({os.path.getsize(output_path)} bytes)")

if __name__ == "__main__":
    generate_og_image()
