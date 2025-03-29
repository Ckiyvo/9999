# 6666/project/app/views.py
import os
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Project, ProjectFile

ALLOWED_FILE_EXTENSIONS = {
    'text': ['.txt', '.pdf', '.doc', '.docx', '.csv'],
    'image': ['.jpg', '.jpeg', '.png'],
    'audio': ['.wav', '.mp3'],
    'video': ['.aac', '.mp4']
}

@csrf_exempt
def upload_files(request, project_name):
    if request.method == 'POST':
        try:
            project = Project.objects.get(name=project_name)
            project_type = project.type
            print('当前项目类型为:',project_type)
            allowed_extensions = ALLOWED_FILE_EXTENSIONS.get(project_type, [])
            files = request.FILES.getlist('files')
            valid_files = []
            invalid_files = []

            for file in files:
                file_extension = os.path.splitext(file.name)[1].lower()
                if file_extension in allowed_extensions:
                    valid_files.append(file)
                else:
                    invalid_files.append(file.name)

            if invalid_files:
                return JsonResponse({'message': f'以下文件类型不允许上传: {", ".join(invalid_files)}'}, status=400)

            project_folder = os.path.join(settings.MEDIA_ROOT, project_name)
            os.makedirs(project_folder, exist_ok=True)

            for file in valid_files:
                file_path = os.path.join(project_folder, file.name)
                with open(file_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
                ProjectFile.objects.create(
                    project=project,
                    file_name=file.name,
                    status='待处理',
                    local_path=file_path
                )

            return JsonResponse({'message': '文件上传成功'})
        except Project.DoesNotExist:
            return JsonResponse({'message': '项目不存在'}, status=404)

    return JsonResponse({'message': '无效的请求方法'}, status=400)

@csrf_exempt
def create_project(request):
    if request.method == 'POST':
        project_name = request.POST.get('project_name')
        project_type = request.POST.get('project_type')  # 获取项目类型
        if not project_name:
            return JsonResponse({'message': '项目名称不能为空'}, status=400)
        if not project_type:
            return JsonResponse({'message': '项目类型不能为空'}, status=400)

        # 处理文件上传
        files = request.FILES.getlist('files')
        valid_files = []
        invalid_files = []
        allowed_extensions = ALLOWED_FILE_EXTENSIONS.get(project_type.lower(), [])

        for file in files:
            file_extension = os.path.splitext(file.name)[1].lower()
            if file_extension in allowed_extensions:
                valid_files.append(file)
            else:
                invalid_files.append(file.name)

        if invalid_files:
            return JsonResponse({'message': f'以下文件类型不允许上传: {", ".join(invalid_files)}'}, status=400)

        project, created = Project.objects.get_or_create(name=project_name, type=project_type)  # 记录项目类型
        project_folder = os.path.join(settings.MEDIA_ROOT, project_name)
        os.makedirs(project_folder, exist_ok=True)

        file_list = []
        for index, file in enumerate(valid_files, start=1):
            file_path = os.path.join(project_folder, file.name)
            with open(file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            # 创建 ProjectFile 实例
            project_file = ProjectFile.objects.create(
                project=project,
                file_name=file.name,
                status='待处理',
                local_path=file_path
            )
            file_list.append({
                'id': project_file.id,
                'name': file.name,
                'status': '待处理',
                'processed_at': '',
                'local_path': project_file.local_path
            })

        return JsonResponse({'message': '项目创建成功', 'files': file_list})

    return JsonResponse({'message': '无效的请求方法'}, status=400)

@csrf_exempt
# 传递 projects 信息
def get_projects(request):
    if request.method == 'GET':
        projects = Project.objects.all()
        project_list = []
        for project in projects:
            project_files = ProjectFile.objects.filter(project=project)
            file_list = []
            for file in project_files:
                file_list.append({
                    'id': file.id,
                    'name': file.file_name,
                    'status': file.status,
                    'processed_at': file.processed_at.strftime('%Y-%m-%d %H:%M:%S') if file.processed_at else '',
                    'local_path': file.local_path
                })
            project_data = {
                'id': project.id,
                'name': project.name,
                'type': project.type,  # 返回项目类型
                'created_at': project.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'files': file_list
            }
            project_list.append(project_data)
        return JsonResponse({'projects': project_list})
    return JsonResponse({'message': '无效的请求方法'}, status=400)

@csrf_exempt
# 显示项目列表具体信息
def get_project_list(request):
    projects = Project.objects.all()
    project_list = []
    for project in projects:
        project_data = {
            'id': project.id,
            'name': project.name,
            'type': project.type,  # 返回项目类型
            'created_at': project.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        project_list.append(project_data)
    return JsonResponse({'projects': project_list})

@csrf_exempt
def get_project_files(request, project_name):
    if request.method == 'GET':
        try:
            project = Project.objects.get(name=project_name)
            project_files = ProjectFile.objects.filter(project=project)
            file_list = []
            for file in project_files:
                file_list.append({
                    'id': file.id,
                    'name': file.file_name,
                    'status': file.status,
                    'processed_at': file.processed_at.strftime('%Y-%m-%d %H:%M:%S') if file.processed_at else '',
                    'local_path': file.local_path
                })
            return JsonResponse({'files': file_list, 'project_type': project.type})  # 返回项目类型
        except Project.DoesNotExist:
            return JsonResponse({'message': '项目不存在'}, status=404)
    return JsonResponse({'message': '无效的请求方法'}, status=400)


@csrf_exempt
def delete_project(request, project_name):
    if request.method == 'POST':
        try:
            project = Project.objects.get(name=project_name)
            # 删除项目下的所有文件
            project_files = ProjectFile.objects.filter(project=project)
            for file in project_files:
                file_path = file.local_path
                if os.path.exists(file_path):
                    os.remove(file_path)
                file.delete()
            # 删除项目
            project.delete()
            return JsonResponse({'message': '项目删除成功'})
        except Project.DoesNotExist:
            return JsonResponse({'message': '项目不存在'}, status=404)
    return JsonResponse({'message': '无效的请求方法'}, status=400)


@csrf_exempt
def delete_file(request, file_id):
    if request.method == 'POST':
        try:
            file = ProjectFile.objects.get(id=file_id)
            file.delete()
            return JsonResponse({'message': '文件删除成功'})
        except ProjectFile.DoesNotExist:
            return JsonResponse({'message': '文件不存在'}, status=404)
    return JsonResponse({'message': '无效的请求方法'}, status=400)

@csrf_exempt
def get_file_content(request, project_name, filename):
    if request.method == 'GET':
        try:
            project = Project.objects.get(name=project_name)
            project_file = ProjectFile.objects.get(project=project, file_name=filename)
            file_path = project_file.local_path
            if os.path.exists(file_path):
                with open(file_path, 'rb') as file:
                    content = file.read()
                # 根据文件类型设置响应头
                file_extension = os.path.splitext(filename)[1].lower()
                if file_extension in ['.txt', '.csv']:
                    content_type = 'text/plain'
                elif file_extension in ['.pdf']:
                    content_type = 'application/pdf'
                elif file_extension in ['.jpg', '.jpeg', '.png']:
                    content_type = f'image/{file_extension[1:]}'
                elif file_extension in ['.wav', '.mp3']:
                    content_type = f'audio/{file_extension[1:]}'
                elif file_extension in ['.aac', '.mp4']:
                    content_type = f'video/{file_extension[1:]}'
                else:
                    content_type = 'application/octet-stream'

                response = HttpResponse(content, content_type=content_type)
                response['Content-Disposition'] = f'inline; filename={filename}'
                return response
            else:
                return JsonResponse({'message': '文件不存在'}, status=404)
        except Project.DoesNotExist:
            return JsonResponse({'message': '项目不存在'}, status=404)
        except ProjectFile.DoesNotExist:
            return JsonResponse({'message': '文件不存在'}, status=404)
    return JsonResponse({'message': '无效的请求方法'}, status=400)