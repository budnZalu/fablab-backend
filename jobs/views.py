from django.shortcuts import render


JOBS = [
    {
        'id': 1,
        'name': 'Двухэкструдерная 3D печать',
        'info': ('Использование двухэкструдерного 3D принтера просто '
                 'необходимо, при печати сложных 3D моделей с '
                 'растворяемыми поддержками.'),
        'price': 700,
        'image': 'http://127.0.0.1:9000/fablab/ex3d2.jpeg'
    },
    {
        'id': 2,
        'name': 'Одноэкструдерная 3D печать',
        'info': ('Печать с использованием одноэкструдного 3D принтера, '
                 'отлично подойдёт для печати простых деталей и моделей.'),
        'price': 500,
        'image': 'http://127.0.0.1:9000/fablab/ex3d.png'
    },
    {
        'id': 3,
        'name': '3D сканирование объекта',
        'info': ('Сканирование позволяет пользователям либо воспроизвести '
                 'деталь путём обратного проектирования, '
                 'либо проверить её путём анализа размеров.'),
        'price': 300,
        'image': 'http://127.0.0.1:9000/fablab/scan.png'
    },
    {
        'id': 4,
        'name': 'Шлифовка детали/модели',
        'info': ('Шлифовка детали на профессиональном шлифовальном станке '
                 'для выравнивания краёв и коррекции формы модели.'),
        'price': 500,
        'image': 'http://127.0.0.1:9000/fablab/correction.png'
    }
]

PRINTINGS = [
    {
        'id': 1,
        'status': 'draft',
        'name': 'Иван Иванов'
    }
]


def index(request):
    job_name = request.GET.get('job_name', '').lower()
    if job_name:
        data = [job for job in JOBS if job_name in job['name'].lower()]
    else:
        data = JOBS
    return render(
        request,
        'index.html',
        context={'jobs': data}
    )


def job_detail(request, pk):
    return render(
        request,
        'job.html',
        context={'job': JOBS[int(pk) - 1]}
    )


def printing_detail(request, pk):
    return render(
        request,
        'printing.html',
        context={'printing': PRINTINGS[pk - 1],
                 'jobs': [job for job in JOBS if job['id'] in [1, 3]]
                 }
    )
