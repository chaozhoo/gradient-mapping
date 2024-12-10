from PIL import Image
import os

def verify_ico(ico_path):
    try:
        # 获取绝对路径
        abs_path = os.path.abspath(ico_path)
        print(f"图标文件绝对路径: {abs_path}")
        
        # 检查文件是否存在
        if not os.path.exists(abs_path):
            print("错误：文件不存在！")
            return False
            
        # 打开并验证图标文件
        with Image.open(abs_path) as img:
            # 输出图标包含的所有尺寸
            if hasattr(img, 'n_frames'):
                print(f"图标包含 {img.n_frames} 个尺寸变体")
                for i in range(img.n_frames):
                    img.seek(i)
                    print(f"尺寸 {i+1}: {img.size}")
            else:
                print(f"单一尺寸: {img.size}")
            return True
            
    except Exception as e:
        print(f"验证过程出错: {str(e)}")
        return False

if __name__ == "__main__":
    verify_ico("gradient-mapper_16x16.ico")