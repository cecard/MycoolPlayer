try:
    from PIL import Image, ImageDraw
    print("Starting icon generation...")

    # 1. Setup canvas
    size = (256, 256)
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 2. Draw Cyan Circle background
    accent_color = (0, 255, 213, 255) 
    draw.ellipse([(10, 10), (246, 246)], fill=accent_color)

    # 3. Draw White Note
    white = (255, 255, 255, 255)
    # Bars and Note heads
    draw.rectangle([(70, 60), (90, 180)], fill=white)
    draw.rectangle([(150, 60), (170, 180)], fill=white)
    draw.rectangle([(70, 60), (170, 90)], fill=white)
    draw.ellipse([(50, 150), (110, 210)], fill=white)
    draw.ellipse([(130, 150), (190, 210)], fill=white)

    # 4. Save
    img.save('app.ico', format='ICO', sizes=[(256, 256), (128, 128)])
    print("Icon app.ico created successfully.")

except Exception as e:
    # Print error without complex formatting to avoid encoding crashes
    print("Error during icon generation.")
    import sys
    sys.exit(1)
