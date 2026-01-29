from rest_framework.views import APIView
from rest_framework.response import Response
from .models import ArticleExplanation

class ExplanationView(APIView):
    def get(self, request, article_id):
        # 쿼리 파라미터로 level을 받음 (예: /?level=3)
        user_level = request.query_params.get('level', 1)
        
        explanation = ArticleExplanation.objects.filter(
            article_id=article_id, 
            level=user_level
        ).first()
        
        if not explanation:
            return Response({"message": "해당 난이도의 해설이 없습니다."}, status=404)
            
        return Response({
            "background": explanation.background_text,
            "detail": explanation.detail_text
        })