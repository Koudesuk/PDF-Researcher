from PIL import Image
import io


def crop_image_left_side(image_data: bytes, keep_percentage: float = 0.6) -> bytes:
    """
    裁剪圖片，只保留左側指定百分比的內容

    Args:
        image_data (bytes): 輸入的圖片二進制數據
        keep_percentage (float): 要保留的左側比例，默認為 0.6 (60%)

    Returns:
        bytes: 裁剪後的圖片二進制數據
    """
    try:
        # 從二進制數據創建圖片對象
        img = Image.open(io.BytesIO(image_data))

        # 計算新的寬度
        new_width = int(img.width * keep_percentage)

        # 裁剪圖片
        cropped_img = img.crop((0, 0, new_width, img.height))

        # 將裁剪後的圖片轉換回二進制數據
        output_buffer = io.BytesIO()
        cropped_img.save(output_buffer, format=img.format or 'PNG')

        return output_buffer.getvalue()

    except Exception as e:
        raise Exception(f"圖片裁剪失敗: {str(e)}")
