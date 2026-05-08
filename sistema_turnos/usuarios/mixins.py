from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from .permissions import (
    es_superadmin,
    usuario_puede_gestionar_negocio,
    usuario_puede_gestionar_operacion,
)


class UserFormKwargsMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class LoginRequiredUserFormMixin(LoginRequiredMixin, UserFormKwargsMixin):
    pass


class SuperadminRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not es_superadmin(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class GestionNegocioObjectRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        negocio = getattr(obj, "negocio", obj)
        if not usuario_puede_gestionar_negocio(request.user, negocio):
            raise PermissionDenied
        self.object = obj
        return super().dispatch(request, *args, **kwargs)


class GestionOperacionObjectRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        negocio = getattr(obj, "negocio", obj)
        if not usuario_puede_gestionar_operacion(request.user, negocio):
            raise PermissionDenied
        self.object = obj
        return super().dispatch(request, *args, **kwargs)


class GestionNegocioFormRequiredMixin:
    def form_valid(self, form):
        negocio = form.cleaned_data.get("negocio") or getattr(form.instance, "negocio", None)
        if not usuario_puede_gestionar_negocio(self.request.user, negocio):
            raise PermissionDenied
        return super().form_valid(form)


class GestionOperacionFormRequiredMixin:
    def form_valid(self, form):
        negocio = form.cleaned_data.get("negocio") or getattr(form.instance, "negocio", None)
        if not usuario_puede_gestionar_operacion(self.request.user, negocio):
            raise PermissionDenied
        return super().form_valid(form)
