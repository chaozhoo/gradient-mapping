import sys
import json
from pathlib import Path
from PIL import Image
import numpy as np
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL.ImageTk import PhotoImage
import re

class GradientMapper:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("图像渐变映射工具")
        self.window.geometry("1200x800")
        
        # Configure window resize behavior
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        
        self.gradient_settings = None
        self.original_image = None
        self.preview_image = None
        self.color_mode = tk.StringVar(value="HEX")
        self.custom_position = tk.BooleanVar(value=False)
        
        self.setup_ui()
        
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(1, weight=1)  # Preview column expands
        main_frame.rowconfigure(0, weight=1)
        
        # 左侧输入区域
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        left_frame.columnconfigure(0, weight=1)
        
        # 按钮区域
        btn_frame = ttk.Frame(left_frame)
        btn_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        btn_frame.columnconfigure(1, weight=1)  # Make buttons stay left
        
        ttk.Button(btn_frame, text="选择图片", command=self.load_image).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="保存结果", command=self.save_result).grid(row=0, column=1, padx=5)
        
        # 模式选择
        mode_frame = ttk.Frame(left_frame)
        mode_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Radiobutton(mode_frame, text="HEX 模式", variable=self.color_mode, 
                       value="HEX", command=self.on_mode_change).grid(row=0, column=0, padx=5)
        ttk.Radiobutton(mode_frame, text="RGB 模式", variable=self.color_mode, 
                       value="RGB", command=self.on_mode_change).grid(row=0, column=1, padx=5)
        
        # 添加自定义位置开关
        ttk.Checkbutton(mode_frame, text="自定义位置", 
                       variable=self.custom_position,
                       command=self.toggle_custom_position).grid(row=0, column=2, padx=5)
        
        # 颜色列表输入
        color_list_frame = ttk.LabelFrame(left_frame, text="颜色列表", padding="5")
        color_list_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        color_list_frame.columnconfigure(0, weight=1)
        
        self.color_list_text = tk.Text(color_list_frame, height=24)
        self.color_list_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.color_list_text.bind("<KeyRelease>", self.sync_color_entries)
        
        # 动态颜色条目
        entries_frame = ttk.LabelFrame(left_frame, text="颜色条目", padding="5")
        entries_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        entries_frame.columnconfigure(0, weight=1)
        
        # 添加按钮
        add_btn_frame = ttk.Frame(entries_frame)
        add_btn_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        add_btn_frame.columnconfigure(0, weight=1)
        
        ttk.Button(add_btn_frame, text="添加颜色", 
                  command=self.add_color_entry).grid(row=0, column=0, pady=5)
        
        # 在颜色条目区域添加反转按钮
        entries_control_frame = ttk.Frame(entries_frame)
        entries_control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        entries_control_frame.columnconfigure(1, weight=1)
        
        ttk.Button(entries_control_frame, text="添加颜色", 
                  command=self.add_color_entry).grid(row=0, column=0, pady=5, padx=5)
        ttk.Button(entries_control_frame, text="反转顺序", 
                  command=self.reverse_gradient).grid(row=0, column=1, pady=5, padx=5)
        
        # 颜色条目容器（可滚动）
        self.entries_canvas = tk.Canvas(entries_frame)
        scrollbar = ttk.Scrollbar(entries_frame, orient="vertical", 
                                command=self.entries_canvas.yview)
        self.color_entries_frame = ttk.Frame(self.entries_canvas)
        
        self.entries_canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.entries_canvas.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.entries_canvas.create_window((0, 0), window=self.color_entries_frame, 
                                        anchor='nw', tags="self.color_entries_frame")
        
        self.color_entries_frame.bind("<Configure>", self.on_frame_configure)
        entries_frame.rowconfigure(1, weight=1)
        
        # 右侧预览区域
        preview_frame = ttk.LabelFrame(main_frame, text="预览", padding="5")
        preview_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.grid(row=0, column=0)

    def on_frame_configure(self, event=None):
        self.entries_canvas.configure(scrollregion=self.entries_canvas.bbox("all"))
        
    def add_color_entry(self):
        colors = self.color_list_text.get("1.0", tk.END).strip().split("\n")
        new_color = "#000000" if self.color_mode.get() == "HEX" else "0,0,0"
        
        if self.custom_position.get():
            # 添加带位置信息的新颜色
            if colors and colors != ['']:
                new_position = 1.0
            else:
                new_position = 0.0
            colors.append(f"[{new_position:.6f}]{new_color}")
        else:
            colors.append(new_color)
        
        self.color_list_text.delete("1.0", tk.END)
        self.color_list_text.insert(tk.END, "\n".join(colors))
        self.sync_color_entries()
        
    def create_color_entry(self, position, color, index):
        entry_frame = ttk.Frame(self.color_entries_frame)
        entry_frame.grid(row=index, column=0, sticky=(tk.W, tk.E), pady=2)
        entry_frame.columnconfigure(1, weight=1)
        
        if self.custom_position.get():
            # 位置输入框
            pos_entry = ttk.Entry(entry_frame, width=10)
            pos_entry.insert(0, f"{position:.6f}")
            pos_entry.grid(row=0, column=0, padx=5)
            pos_entry.bind("<KeyRelease>", lambda e, i=index: self.update_position(e, i))
        else:
            # 位置标签
            pos_label = ttk.Label(entry_frame, text=f"位置: {position:.6f}")
            pos_label.grid(row=0, column=0, padx=5)
        
        color_entry = ttk.Entry(entry_frame)
        color_entry.insert(0, color)
        color_entry.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        color_entry.bind("<KeyRelease>", self.update_color_list)
        
        del_button = ttk.Button(entry_frame, text="删除", 
                               command=lambda e=entry_frame: self.delete_color_entry(e))
        del_button.grid(row=0, column=2, padx=5)
        
        return entry_frame

    def toggle_custom_position(self):
        """切换自定义位置模式时更新界面"""
        if self.custom_position.get():
            # 将当前颜色列表转换为带位置格式
            colors = self.color_list_text.get("1.0", tk.END).strip().split("\n")
            if not colors or colors == ['']:
                return
                
            num_colors = len(colors)
            formatted_colors = []
            for i, color in enumerate(colors):
                position = i / (num_colors - 1) if num_colors > 1 else 0
                formatted_colors.append(f"[{position:.6f}]{color}")
            
            self.color_list_text.delete("1.0", tk.END)
            self.color_list_text.insert(tk.END, "\n".join(formatted_colors))
        else:
            # 移除位置信息
            colors = self.color_list_text.get("1.0", tk.END).strip().split("\n")
            stripped_colors = [color.split("]")[1] for color in colors if "]" in color]
            
            self.color_list_text.delete("1.0", tk.END)
            self.color_list_text.insert(tk.END, "\n".join(stripped_colors))
            
        self.sync_color_entries()

    def update_position(self, event, index):
        """更新指定索引的位置值"""
        try:
            new_position = float(event.widget.get())
            if 0 <= new_position <= 1:
                colors = self.color_list_text.get("1.0", tk.END).strip().split("\n")
                color = colors[index].split("]")[1]
                colors[index] = f"[{new_position:.6f}]{color}"
                
                self.color_list_text.delete("1.0", tk.END)
                self.color_list_text.insert(tk.END, "\n".join(colors))
                self.update_preview()
        except ValueError:
            pass

    def sync_color_entries(self, event=None):
        # Clear existing entries
        for widget in self.color_entries_frame.winfo_children():
            widget.destroy()
        
        # Get color list
        colors = self.color_list_text.get("1.0", tk.END).strip().split("\n")
        if not colors or colors == ['']:
            return
            
        num_colors = len(colors)
        
        if self.custom_position.get():
            # Parse position and color from formatted strings
            for i, line in enumerate(colors):
                if "]" in line:
                    pos_str, color = line.split("]")
                    position = float(pos_str[1:])
                    self.create_color_entry(position, color, i)
        else:
            # Use default positions
            for i, color in enumerate(colors):
                color = color.split("]")[1] if "]" in color else color
                position = i / (num_colors - 1) if num_colors > 1 else 0
                self.create_color_entry(position, color, i)
        
        self.update_preview()
    
    def update_color_list(self, event=None):
        entries = self.color_entries_frame.winfo_children()
        colors = []
        
        for entry_frame in entries:
            if self.custom_position.get():
                position = float(entry_frame.winfo_children()[0].get())
                color = entry_frame.winfo_children()[1].get()
                colors.append(f"[{position:.6f}]{color}")
            else:
                color = entry_frame.winfo_children()[1].get()
                colors.append(color)
        
        self.color_list_text.delete("1.0", tk.END)
        self.color_list_text.insert(tk.END, "\n".join(colors))
        self.update_preview()
    
    def delete_color_entry(self, entry_frame):
        entry_frame.destroy()
        self.update_color_list()
    
    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if file_path:
            try:
                self.original_image = Image.open(file_path)
                self.update_preview()
            except Exception as e:
                messagebox.showerror("错误", f"加载图片失败：{str(e)}")
    
    def apply_gradient(self, image):
        if not self.gradient_settings or not image:
            return None
            
        # 转换为灰度图
        gray_image = image.convert('L')
        img_array = np.array(gray_image) / 255.0
        
        # 获取渐变设置
        gradient = self.gradient_settings['gradient']
        
        # 创建输出图像
        result = np.zeros((*img_array.shape, 3), dtype=np.uint8)
        
        for i in range(len(gradient)-1):
            pos1, color1 = gradient[i]['position'], gradient[i]['color']
            pos2, color2 = gradient[i+1]['position'], gradient[i+1]['color']
            
            # 解析颜色
            if self.color_mode.get() == "HEX":
                # 如果是自定义位置模式，需要去除位置信息
                if ']' in color1:
                    color1 = color1.split(']')[1]
                if ']' in color2:
                    color2 = color2.split(']')[1]
                    
                r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
                r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
            else:  # RGB
                # 如果是自定义位置模式，需要去除位置信息
                if ']' in color1:
                    color1 = color1.split(']')[1]
                if ']' in color2:
                    color2 = color2.split(']')[1]
                    
                r1, g1, b1 = map(int, color1.split(","))
                r2, g2, b2 = map(int, color2.split(","))
            
            mask = (img_array >= pos1) & (img_array < pos2)
            ratio = (img_array[mask] - pos1) / (pos2 - pos1)
            
            result[mask, 0] = (r1 + (r2 - r1) * ratio).astype(np.uint8)
            result[mask, 1] = (g1 + (g2 - g1) * ratio).astype(np.uint8)
            result[mask, 2] = (b1 + (b2 - b1) * ratio).astype(np.uint8)
            
        return Image.fromarray(result)
    
    def update_preview(self):
        if self.original_image:
            # 更新渐变设置
            colors = self.color_list_text.get("1.0", tk.END).strip().split("\n")
            if not colors or colors == ['']:
                return
            
            gradient_list = []
            if self.custom_position.get():
                # 解析带位置信息的颜色
                for color_str in colors:
                    if ']' in color_str:
                        pos_str, color = color_str.split(']')
                        position = float(pos_str[1:])
                        gradient_list.append({"position": position, "color": color})
            else:
                # 使用默认位置
                num_colors = len(colors)
                for i, color in enumerate(colors):
                    position = i / (num_colors - 1) if num_colors > 1 else 0
                    gradient_list.append({"position": position, "color": color})
            
            self.gradient_settings = {"gradient": gradient_list}
            
            result = self.apply_gradient(self.original_image)
            if result:
                # 调整预览大小
                preview_size = (400, 400)
                result.thumbnail(preview_size, Image.LANCZOS)
                self.preview_image = PhotoImage(result)
                self.preview_label.configure(image=self.preview_image)
    
    def save_result(self):
        if not self.original_image or not self.gradient_settings:
            messagebox.showwarning("警告", "请先加载图片和渐变配置")
            return
            
        result = self.apply_gradient(self.original_image)
        if result:
            original_path = Path(self.original_image.filename)
            new_path = original_path.parent / f"{original_path.stem}_gradient{original_path.suffix}"
            result.save(new_path)
            messagebox.showinfo("成功", f"已保存至：{new_path}")
    
    def run(self):
        self.window.mainloop()

    def hex_to_rgb(self, hex_color):
        """将HEX颜色转换为RGB格式"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"{r},{g},{b}"

    def rgb_to_hex(self, rgb_color):
        """将RGB颜色转换为HEX格式"""
        r, g, b = map(int, rgb_color.split(','))
        return f"#{r:02x}{g:02x}{b:02x}"

    def convert_color(self, color, to_mode):
        """转换颜色格式"""
        if ']' in color:  # 带位置信息
            pos, color_value = color.split(']')
            pos = pos + ']'
        else:
            pos = ''
            color_value = color

        try:
            if to_mode == "RGB" and color_value.startswith('#'):
                new_color = self.hex_to_rgb(color_value)
            elif to_mode == "HEX" and ',' in color_value:
                new_color = self.rgb_to_hex(color_value)
            else:
                new_color = color_value
        except (ValueError, IndexError):
            # 如果转换失败，保持原值
            new_color = color_value

        return pos + new_color

    def on_mode_change(self):
        """处理颜色模式切换"""
        # 获取当前所有颜色
        colors = self.color_list_text.get("1.0", tk.END).strip().split("\n")
        if not colors or colors == ['']:
            return

        # 转换所有颜色到新模式
        new_mode = self.color_mode.get()
        converted_colors = [self.convert_color(color, new_mode) for color in colors]

        # 更新文本框
        self.color_list_text.delete("1.0", tk.END)
        self.color_list_text.insert(tk.END, "\n".join(converted_colors))

        # 更新颜色条目
        self.sync_color_entries()

    def reverse_gradient(self):
        """反转渐变顺序"""
        colors = self.color_list_text.get("1.0", tk.END).strip().split("\n")
        if not colors or colors == ['']:
            return
        
        if self.custom_position.get():
            # 处理带位置信息的颜色
            reversed_colors = []
            for color in reversed(colors):
                if ']' in color:
                    pos_str, color_value = color.split(']')
                    pos = float(pos_str[1:])
                    # 反转位置值
                    new_pos = 1.0 - pos
                    reversed_colors.append(f"[{new_pos:.6f}]{color_value}")
                else:
                    reversed_colors.append(color)
        else:
            # 直接反转颜色顺序
            reversed_colors = list(reversed(colors))
        
        # 更新文本框
        self.color_list_text.delete("1.0", tk.END)
        self.color_list_text.insert(tk.END, "\n".join(reversed_colors))
        
        # 更新颜色条目和预览
        self.sync_color_entries()

if __name__ == "__main__":
    app = GradientMapper()
    app.run()
