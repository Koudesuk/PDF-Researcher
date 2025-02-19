from deep_translator import GoogleTranslator
import os
import time
from rich.console import Console
from rich.traceback import install

# TODO: Fix the issue that the translate func is not working inside docker container.

# 安装 rich 的異常處理器
install(show_locals=True)

# 創建 rich console 實例
console = Console()

# 定義支援的語言（與 app.py 保持一致）
SUPPORTED_LANGUAGES = {
    'zh-TW': 'zh-TW',  # Traditional Chinese
    'zh-CN': 'zh-CN',  # Simplified Chinese
    'en': 'en',        # English
    'ja': 'ja',        # Japanese
    'ko': 'ko',        # Korean
}


class TranslationError(Exception):
    """翻譯相關的基礎異常"""
    pass


def translate_text(text: str, target_language: str = 'zh-TW') -> str:
    """
    翻譯文本到目標語言

    Args:
        text (str): 要翻譯的文本
        target_language (str): 目標語言代碼 (預設: 'zh-TW' 繁體中文)

    Returns:
        str: 翻譯後的文本

    Raises:
        TranslationError: 翻譯失敗時拋出
        ValueError: 輸入參數無效時拋出
    """
    try:
        # 驗證目標語言
        if target_language not in SUPPORTED_LANGUAGES:
            raise ValueError(f"不支援的目標語言：{target_language}")

        # 取得目標語言代碼
        target = SUPPORTED_LANGUAGES[target_language]

        # 從環境變量中獲取重試次數和等待時間
        retry_count = int(os.getenv('GOOGLETRANS_RETRY', 3))
        wait_time = int(os.getenv('GOOGLETRANS_TIMEOUT', 5))

        # 嘗試翻譯，如果失敗則重試
        last_error = None
        for attempt in range(retry_count):
            try:
                # 創建翻譯器實例
                translator = GoogleTranslator(source='auto', target=target)

                # 進行翻譯
                translated_text = translator.translate(text)

                # 驗證翻譯結果
                if not translated_text:
                    raise TranslationError("翻譯服務返回空結果")

                translated_text = translated_text.strip()
                if not translated_text:
                    raise TranslationError("翻譯結果為空")

                # 檢查翻譯結果是否有效
                source_text = text.strip().lower()
                if translated_text.lower() == source_text:
                    raise TranslationError("翻譯結果與原文相同，可能是服務暫時不可用")

                console.print(f"[green]翻譯嘗試 {attempt + 1} 成功[/green]")
                return translated_text

            except Exception as e:
                last_error = e
                if attempt < retry_count - 1:
                    console.print(
                        f"[yellow]翻譯嘗試 {attempt + 1} 失敗: {str(e)}[/yellow]")
                    console.print(f"[blue]等待 {wait_time} 秒後重試...[/blue]")
                    time.sleep(wait_time)
                    wait_time *= 2  # 指數退避策略
                continue

        # 如果所有重試都失敗了
        error_msg = f"翻譯在 {retry_count} 次嘗試後失敗"
        console.print(f"[red]{error_msg}[/red]")
        console.print(f"[red]最後一次錯誤：{str(last_error)}[/red]")
        raise TranslationError(error_msg)

    except ValueError as ve:
        console.print(f"[red]輸入驗證錯誤：{str(ve)}[/red]")
        raise

    except TranslationError as te:
        console.print(f"[red]翻譯錯誤：{str(te)}[/red]")
        raise

    except Exception as e:
        error_msg = f"翻譯過程發生未預期的錯誤：{str(e)}"
        console.print(f"[red]{error_msg}[/red]")
        raise TranslationError(error_msg)
