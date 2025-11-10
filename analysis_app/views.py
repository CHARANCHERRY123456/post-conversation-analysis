from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
import json
# Create your views here.
@api_view(['POST','GET'])
def upload_file(request):
    print("HI")
    file_obj = request.FILES.get('file')
    # print the json file
    if file_obj:
        json_file = json.load(file_obj)
        # save json file to local folders
        with open('uploaded_file.json', 'w') as f:
            json.dump(json_file, f)

    print(file_obj)
    return Response("Hello, world. You're at the upload file view.")
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        print(f"Received file: {uploaded_file.name}")
        print(uploaded_file.read())
        return render(request, 'upload_success.html', {'filename': uploaded_file.name})
    return render(request, 'upload.html')