try:
    from PIL import Image, ImageDraw
    print("正在生成图标...")

    # 1. 配置画布 (256x256)
    size = (256, 256)
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 2. 绘制赛博朋克青色圆底 (#00FFD5)
    # 留出一点边距防止贴边
    accent_color = (0, 255, 213, 255) 
    draw.ellipse([(10, 10), (246, 246)], fill=accent_color)

    # 3. 绘制白色极简音符
    white = (255, 255, 255, 255)
    
    # 左竖线
    draw.rectangle([(70, 60), (90, 180)], fill=white)
    # 右竖线
    draw.rectangle([(150, 60), (170, 180)], fill=white)
    # 横梁
    draw.rectangle([(70, 60), (170, 90)], fill=white)
    # 左音符头 (圆形)
    draw.ellipse([(50, 150), (110, 210)], fill=white)
    # 右音符头 (圆形)
    draw.ellipse([(130, 150), (190, 210)], fill=white)

    # 4. 保存为 ICO 格式
    img.save('app.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print("✅ 图标 app.ico 生成成功！")

except ImportError:
    print("❌ 错误: 没有安装 Pillow 库")
    exit(1)
except Exception as e:
    print(f"❌ 生成失败: {e}")
    exit(1)
