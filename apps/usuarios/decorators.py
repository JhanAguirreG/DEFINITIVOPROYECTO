from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect



def rol_requerido(roles_permitidos):
    """
    Decorador para restringir vistas según el rol del usuario.

    Ejemplo:
    @rol_requerido(["SUPERADMIN"])
    """


    def decorator(view_func):


        @wraps(view_func)
        def wrapper(request, *args, **kwargs):


            if not request.user.is_authenticated:

                return redirect("login")



            if request.user.rol in roles_permitidos:

                return view_func(
                    request,
                    *args,
                    **kwargs
                )



            messages.error(
                request,
                "No tiene permisos para acceder a esta sección."
            )


            return redirect(
                "dashboard"
            )



        return wrapper



    return decorator