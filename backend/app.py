from rich.traceback import install
from rich.panel import Panel
from rich.console import Console
from rich import print as rprint
from flask_cors import CORS
from flask import Flask, request, jsonify
from utils.embedding_pdf import PDFEmbedder
from utils.crop import crop_image_left_side
from utils.translate import translate_text, TranslationError, SUPPORTED_LANGUAGES
from utils.chatlog import ChatLogger
import os
import datetime
import base64
import json
from utils.Agent import ResearchAgent

# RAG Function狀態
EnableChatWithPicture = False
EnableWebResearch = False

# 安裝 rich 的異常追蹤
install(show_locals=True)

# 創建 rich console 實例
console = Console()

# Flask app initialization
app = Flask(__name__)
CORS(app)

# PDF files upload directory
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Screenshots directory
SCREENSHOTS_DIR = 'screenshots'
if not os.path.exists(SCREENSHOTS_DIR):
    os.makedirs(SCREENSHOTS_DIR)

# Dialog directory
DIALOG_DIR = 'logs'
if not os.path.exists(DIALOG_DIR):
    os.makedirs(DIALOG_DIR)

# PDFEmbedder instance
embedder = PDFEmbedder()

# Initialize ChatLogger
chat_logger = ChatLogger(DIALOG_DIR)

# Initialize the Research Agent
agent = ResearchAgent()


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and file.filename.endswith('.pdf'):
        filename = os.path.join(UPLOAD_FOLDER, file.filename)

        # 檢查檔案是否已存在
        if os.path.exists(filename):
            try:
                # 儲存新上傳的檔案到臨時位置
                temp_filename = os.path.join(
                    UPLOAD_FOLDER, 'temp_' + file.filename)
                file.save(temp_filename)

                # 比較檔案內容
                import filecmp
                if filecmp.cmp(filename, temp_filename, shallow=False):
                    # 如果內容相同，刪除臨時檔案
                    os.remove(temp_filename)
                    return jsonify({
                        'message': 'File already exists and content is identical',
                        'filename': file.filename,
                        'status': 'exists'
                    }), 200
                else:
                    # 如果內容不同，使用新檔案取代舊檔案
                    os.replace(temp_filename, filename)
            except Exception as e:
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)
                console.print(Panel(
                    f"[red]Error during file comparison:[/red]\n"
                    f"[yellow]{str(e)}[/yellow]",
                    title="File Comparison Error",
                    border_style="red"
                ))
        else:
            # 如果檔案不存在，直接儲存
            file.save(filename)

        rprint(f"[bold green]Starting embedding process...[/bold green]")
        # Embedding process
        try:
            embd_time = embedder.create_embeddings(filename, force=False)
            if embd_time:
                print("\nEmbedding process completed successfully!")
                print(f"Total processing time: {
                    embedder._format_time(embd_time['total'])}")
        except FileNotFoundError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

        return jsonify({
            'message': 'File uploaded successfully and processed',
            'filename': file.filename,
            'status': 'uploaded'
        }), 200

    return jsonify({'error': 'Invalid file type'}), 400


@app.route('/selected-text', methods=['POST'])
def handle_selected_text():
    try:
        # 1. 請求格式驗證
        if not request.is_json:
            console.print("[red]錯誤：請求內容類型不是 JSON[/red]")
            return jsonify({
                'status': 'error',
                'error_code': 'INVALID_CONTENT_TYPE',
                'message': '請求必須是 JSON 格式'
            }), 415

        data = request.get_json()

        # 2. 請求數據完整性驗證
        if not data:
            console.print("[red]錯誤：請求數據為空[/red]")
            return jsonify({
                'status': 'error',
                'error_code': 'EMPTY_REQUEST',
                'message': '請求數據為空'
            }), 400

        # 3. 必要欄位驗證
        selected_text = data.get('text')
        if not selected_text:
            console.print("[red]錯誤：未提供要翻譯的文本[/red]")
            return jsonify({
                'status': 'error',
                'error_code': 'MISSING_TEXT',
                'message': '未提供要翻譯的文本'
            }), 400

        # 4. 文本長度驗證
        if len(selected_text) > 5000:
            console.print("[red]錯誤：文本超過長度限制[/red]")
            return jsonify({
                'status': 'error',
                'error_code': 'TEXT_TOO_LONG',
                'message': '文本長度超過限制（最大5000字符）'
            }), 400

        page_number = data.get('pageNumber', 'unknown')
        target_language = data.get('targetLanguage', 'zh-TW')

        # 5. 語言支援驗證
        if target_language not in SUPPORTED_LANGUAGES:
            console.print(f"[red]錯誤：不支援的目標語言：{target_language}[/red]")
            return jsonify({
                'status': 'error',
                'error_code': 'UNSUPPORTED_LANGUAGE',
                'message': f'不支援的目標語言。支援的語言：{", ".join(SUPPORTED_LANGUAGES.keys())}'
            }), 400

        # 6. 執行翻譯
        try:
            translated_text = translate_text(selected_text, target_language)

            # 輸出詳細日誌
            console.print(Panel(
                f"[cyan]源文本 (頁碼 {page_number}):[/cyan]\n"
                f"[yellow]{selected_text}[/yellow]\n\n"
                f"[cyan]目標語言:[/cyan] [green]{target_language}[/green]\n\n"
                f"[cyan]翻譯結果:[/cyan]\n"
                f"[blue]{translated_text}[/blue]",
                title="翻譯詳情",
                border_style="green"
            ))

            return jsonify({
                'status': 'success',
                'originalText': selected_text,
                'translatedText': translated_text,
                'targetLanguage': target_language,
                'pageNumber': page_number,
                'message': '文本已成功翻譯'
            }), 200

        except ValueError as e:
            console.print(f"[red]錯誤：輸入驗證失敗 - {str(e)}[/red]")
            return jsonify({
                'status': 'error',
                'error_code': 'VALIDATION_ERROR',
                'message': str(e)
            }), 400

        except TranslationError as e:
            error_msg = str(e)
            console.print(f"[red]錯誤：翻譯服務錯誤 - {error_msg}[/red]")

            if "服務暫時不可用" in error_msg:
                return jsonify({
                    'status': 'error',
                    'error_code': 'SERVICE_UNAVAILABLE',
                    'message': error_msg
                }), 503

            return jsonify({
                'status': 'error',
                'error_code': 'TRANSLATION_ERROR',
                'message': error_msg
            }), 500

    except json.JSONDecodeError:
        console.print("[red]錯誤：無效的 JSON 格式[/red]")
        return jsonify({
            'status': 'error',
            'error_code': 'INVALID_JSON',
            'message': '請求數據格式錯誤'
        }), 400

    except Exception as e:
        console.print(f"[red]錯誤：未預期的錯誤 - {str(e)}[/red]")
        return jsonify({
            'status': 'error',
            'error_code': 'INTERNAL_ERROR',
            'message': f'處理請求時發生錯誤：{str(e)}',
            'details': {
                'error_type': type(e).__name__,
                'error_message': str(e)
            }
        }), 500


@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        pdf_filename = data.get('pdfFilename')

        # 更新全域變數狀態
        global EnableChatWithPicture, EnableWebResearch
        EnableChatWithPicture = data.get('enableChatWithPicture', False)
        EnableWebResearch = data.get('enableWebResearch', False)

        # 使用rich印出接收到的訊息和狀態
        console.print(Panel(
            f"[cyan]Received Message:[/cyan] [yellow]{message}[/yellow]\n"
            f"[cyan]PDF File:[/cyan] [yellow]{pdf_filename or 'None'}[/yellow]\n"
            f"[cyan]EnableChatWithPicture:[/cyan] [green]{EnableChatWithPicture}[/green]\n"
            f"[cyan]EnableWebResearch:[/cyan] [green]{EnableWebResearch}[/green]",
            title="Chat Request Info",
            border_style="blue"
        ))

        if not message:
            return jsonify({'error': 'Empty message'}), 400

        # 使用 ChatLogger 處理完整的對話流程
        def generate_response(msg: str, pdf_filename: str = None,
                              enable_web_research: bool = False,
                              enable_chat_with_picture: bool = False,
                              image_data: str = None) -> str:
            try:
                try:
                    result = agent.process_input(
                        user_input=msg,
                        image_data=image_data,
                        enable_web_research=enable_web_research,
                        enable_chat_with_picture=enable_chat_with_picture,
                        pdf_filename=pdf_filename
                    )
                    return result.get('running_summary', "抱歉，生成回應時發生錯誤。請稍後再試。")
                except Exception as e:
                    console.print(f"[red]處理請求時發生錯誤: {str(e)}[/red]")
                    return f"處理您的請求時發生錯誤。錯誤信息：{str(e)}"
            except Exception as e:
                print(f"Error generating response: {e}")
                return f"抱歉，生成回應時發生錯誤: {str(e)}"

        try:
            # Get image data from screenshots directory if exists
            image_data = None
            if os.path.exists(SCREENSHOTS_DIR):
                png_files = [f for f in os.listdir(
                    SCREENSHOTS_DIR) if f.endswith('.png')]
                if png_files:
                    image_path = os.path.join(SCREENSHOTS_DIR, png_files[0])
                    with open(image_path, 'rb') as img_file:
                        image_data = base64.b64encode(
                            img_file.read()).decode('utf-8')

            # Extract parameters from request
            enable_web_research = data.get('enableWebResearch', False)
            enable_chat_with_picture = data.get('enableChatWithPicture', False)

            _, ai_message = chat_logger.process_chat(
                message=message,
                pdf_filename=pdf_filename,
                response_generator=lambda msg: generate_response(
                    msg=msg,
                    pdf_filename=pdf_filename,
                    enable_web_research=enable_web_research,
                    enable_chat_with_picture=enable_chat_with_picture,
                    image_data=image_data
                )
            )

            # 確保回應格式正確
            if not isinstance(ai_message, dict):
                ai_message = {"response": ai_message}

            return jsonify(ai_message), 200
        except ValueError as ve:
            return jsonify({
                'error': f'回應格式錯誤: {str(ve)}'
            }), 400
        except Exception as e:
            print(f"處理聊天訊息時發生錯誤: {e}")
            return jsonify({
                'error': f'處理聊天訊息時發生錯誤: {str(e)}'
            }), 500

    except Exception as e:
        return jsonify({
            'error': f'Error processing chat message: {str(e)}'
        }), 500


@app.route('/chat-history/<path:filename>', methods=['GET'])
def get_chat_history(filename):
    try:
        messages = chat_logger.load_chat_history(filename)
        return jsonify({
            'messages': messages,
            'pdfFilename': filename
        }), 200
    except Exception as e:
        return jsonify({
            'error': f'Error loading chat history: {str(e)}'
        }), 500


@app.route('/chat-history/<path:filename>', methods=['DELETE'])
def clear_chat_history(filename):
    try:
        chat_logger.clear_chat_history(filename)
        return jsonify({
            'message': 'Chat history cleared successfully'
        }), 200
    except Exception as e:
        return jsonify({
            'error': f'Error clearing chat history: {str(e)}'
        }), 500


@app.route('/chat-history', methods=['DELETE'])
def clear_all_chat_history():
    try:
        chat_logger.clear_chat_history(None)  # None 表示清空所有記錄
        return jsonify({
            'message': 'All chat histories cleared successfully'
        }), 200
    except Exception as e:
        return jsonify({
            'error': f'Error clearing all chat histories: {str(e)}'
        }), 500


@app.route('/upload-screenshot', methods=['POST'])
def upload_screenshot():
    try:
        data = request.get_json()
        if not data or 'screenshot' not in data:
            return jsonify({'error': 'No screenshot data provided'}), 400

        # Get base64 data
        base64_data = data['screenshot']

        # Remove data URL prefix if present
        if ',' in base64_data:
            base64_data = base64_data.split(',')[1]

        # Decode base64 data
        import base64
        image_data = base64.b64decode(base64_data)

        # Clear existing screenshots
        if os.path.exists(SCREENSHOTS_DIR):
            for file in os.listdir(SCREENSHOTS_DIR):
                file_path = os.path.join(SCREENSHOTS_DIR, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")

        # Generate timestamp-based filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'screenshot_{timestamp}.png'
        file_path = os.path.join(SCREENSHOTS_DIR, filename)

        # 裁剪圖片，保留左側 60% 的內容
        cropped_image = crop_image_left_side(image_data)

        # 保存裁剪後的圖片
        with open(file_path, 'wb') as f:
            f.write(cropped_image)

        return jsonify({
            'message': 'Screenshot uploaded successfully',
            'filename': filename
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/')
def health_check():
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    # 使用 Flask 的內建伺服器
    app.run(host='0.0.0.0', port=9999)
