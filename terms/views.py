from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Term

class TermSearchView(APIView):
    def get(self, request):
        query = request.query_params.get('word', '')
        terms = Term.objects.filter(name__icontains=query)
        data = [{"name": t.name, "explanation": t.explanation} for t in terms]
        return Response(data)