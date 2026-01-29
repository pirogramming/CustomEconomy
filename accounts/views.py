from rest_framework.views import APIView
from rest_framework.response import Response
from .models import User, UserBookmark
from articles.models import Article

class UserProfileView(APIView):
    def get(self, request, user_id):
        user = User.objects.get(user_id=user_id)
        # 간단한 프로필 정보 반환
        return Response({
            "nickname": user.nickname,
            "level": user.level,
            "total_score": user.total_score
        })

class MyBookmarkView(APIView):
    def get(self, request, user_id):
        bookmarks = UserBookmark.objects.filter(user_id=user_id).select_related('article')
        data = [{"article_id": b.article.article_id, "title": b.article.title} for b in bookmarks]
        return Response(data)