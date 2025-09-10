# app/controllers/chatbot_controller.py
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from app.utils.decorators import student_required
from app.services.gemini_service import gemini_generate_answer, gemini_extract_grades,gemini_generate_answer_default
from app.services.prediction_service import predict_percent


chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')

@chatbot_bp.route("/process")
@student_required
def serve_index():
    """Phục vụ file chat interface"""
    return render_template('chatbot/process.html')

@chatbot_bp.route("/process", methods=["POST"])
@student_required
def process():
    try:

        if request.is_json:
            data = request.get_json()
        else:
            data = request.form

        question = data.get("question")
        session_id = data.get("session_id")

        if not question:
            return jsonify({"error": "Câu hỏi không được cung cấp"}), 400

        # Lấy user_id (thử cả 2 cách để đảm bảo compatibility)
        user_id = getattr(current_user, 'id', None) or getattr(current_user, 'user_id', None)
        if not user_id:
            return jsonify({"error": "Không thể xác định user"}), 400

        user_id = str(user_id)  # Convert to string cho session management

        # Trích xuất điểm từ câu hỏi bằng Gemini
        input_data = gemini_extract_grades(question)
        if input_data == question:
            print('default - using enhanced RAG with session')

            result = gemini_generate_answer_default(
                question=question,
                user_id=user_id,
                session_id=session_id
            )

            if isinstance(result, dict):
                return jsonify({
                    "answer": result.get("response", result.get("answer", str(result))),
                    "session_id": result.get("session_id"),
                    "ma_sinh_vien": current_user.ma_sv,
                    "success": result.get("success", True)
                })
            else:
                # nếu trả về string
                return jsonify({
                    "answer": result,
                    "ma_sinh_vien": current_user.ma_sv
                })

        percent = predict_percent(input_data)

        # Sinh câu trả lời tự nhiên bằng Gemini
        answer = gemini_generate_answer(percent, current_user.ma_sv)

        return jsonify({
            "ma_sinh_vien": current_user.ma_sv,
            "percent": percent,
            "answer": answer
        })

    except Exception as e:
        print(f"Error in chatbot process: {e}")
        # Fallback error handling với session support
        try:
            user_id = str(getattr(current_user, 'id', None) or getattr(current_user, 'user_id', None) or 'unknown')
            fallback_result = gemini_generate_answer_default(
                question=question or "Xin chào",
                user_id=user_id,
                session_id=None
            )

            if isinstance(fallback_result, dict):
                return jsonify({
                    "answer": fallback_result.get("response", "Xin lỗi, có lỗi xảy ra."),
                    "session_id": fallback_result.get("session_id"),
                    "error": str(e)
                })
            else:
                return jsonify({
                    "answer": fallback_result,
                    "error": str(e)
                })
        except:
            return jsonify({
                "answer": "Xin lỗi, có lỗi xảy ra. Vui lòng thử lại.",
                "error": str(e)
            })

