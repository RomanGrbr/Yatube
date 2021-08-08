from http import HTTPStatus

from django.shortcuts import render


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=HTTPStatus.NOT_FOUND
    )


def server_error(request):
    http_status = HTTPStatus.INTERNAL_SERVER_ERROR
    return render(request, "misc/500.html", status=http_status)
