from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Quiz, QuizResult, QuizChoice
from accounts.models import User

class QuizSubmitView(APIView):
    def post(self, request, quiz_id):
        user_id = request.data.get('user_id')
        selected_choice_id = request.data.get('choice_id')
        
        quiz = Quiz.objects.get(quiz_id=quiz_id)
        choice = QuizChoice.objects.get(choice_id=selected_choice_id)
        user = User.objects.get(user_id=user_id)
        
        # 정답 여부 확인
        is_correct = choice.is_correct
        score = 10 if is_correct else 0
        
        # 결과 저장
        result = QuizResult.objects.create(
            user=user,
            quiz=quiz,
            selected_answer=choice.choice_text,
            is_correct=is_correct,
            earned_score=score
        )
        
        # 사용자 점수 갱신 (선택 사항)
        if is_correct:
            user.total_score += score
            user.save()
            
        return Response({
            "is_correct": is_correct,
            "earned_score": score,
            "explanation": quiz.quizanswer.explanation # QuizAnswer와 OneToOne 관계 활용
        })