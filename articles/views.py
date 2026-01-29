from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Article

class ArticleDetailView(APIView):
    def get(self, request, article_id):
        try:
            article = Article.objects.prefetch_related('terms').get(article_id=article_id)
            
            # 기사와 관련된 용어(terms) 추출
            terms_data = [{"term_id": t.term_id, "name": t.name} for t in article.terms.all()]
            
            return Response({
                "title": article.title,
                "content": article.content,
                "source": article.source,
                "related_terms": terms_data
            })
        except Article.DoesNotExist:
            return Response({"error": "Article not found"}, status=404)