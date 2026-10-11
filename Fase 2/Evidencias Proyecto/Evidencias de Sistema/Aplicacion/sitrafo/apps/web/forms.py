"""Formularios de la aplicacion web del cliente."""
from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
)
from django.db import transaction

from apps.catalogo.models import ModeloProducto, ParametroTecnico
from apps.clientes.models import Cliente, DireccionCliente
from apps.comercial.models import SolicitudPresupuesto
from apps.common.validators import limpiar_rut, validar_rut
from apps.seguridad.models import Usuario

VERSION_POLITICA = "2026-09"


class BootstrapMixin:
    """Aplica las clases de Bootstrap 5 a todos los campos."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            widget = campo.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")


class LoginForm(BootstrapMixin, AuthenticationForm):
    username = forms.CharField(
        label="Nombre de acceso",
        widget=forms.TextInput(attrs={"autofocus": True, "placeholder": "usuario"}),
    )
    password = forms.CharField(
        label="Contrasena",
        widget=forms.PasswordInput(attrs={"placeholder": "********"}),
    )

    def clean(self):
        """Cuenta los intentos fallidos y aplica el bloqueo temporal (RF-SEG-04)."""
        from apps.seguridad.views import mensaje_cuenta_no_disponible, registrar_intento

        usuario = Usuario.objects.filter(username=self.data.get("username", "").strip()).first()
        if usuario:
            usuario.levantar_bloqueo_vencido()
            if usuario.estado == Usuario.Estado.BLOQUEADO:
                raise forms.ValidationError(mensaje_cuenta_no_disponible(usuario),
                                            code="cuenta_bloqueada")
        try:
            datos = super().clean()
        except forms.ValidationError:
            if usuario and self.errors.get("__all__") is None:
                registrar_intento(usuario)
                if usuario.estado == Usuario.Estado.BLOQUEADO:
                    raise forms.ValidationError(mensaje_cuenta_no_disponible(usuario),
                                                code="cuenta_bloqueada") from None
            raise
        if usuario:
            usuario.registrar_acceso_exitoso()
        return datos

    def confirm_login_allowed(self, user):
        """Una cuenta suspendida no puede ingresar (RF-ADM-03)."""
        super().confirm_login_allowed(user)
        if not user.puede_ingresar:
            raise forms.ValidationError(
                "La cuenta se encuentra suspendida. Contacte al area comercial.",
                code="cuenta_suspendida",
            )


class RegistroClienteForm(BootstrapMixin, forms.Form):
    """
    Autorregistro de cliente desde la web (RF-CLI-06).

    Crea el cliente y su cuenta de acceso en una sola transaccion.
    """

    rut = forms.CharField(
        label="RUT de la empresa o persona",
        max_length=12,
        help_text="Formato 12345678-9",
    )
    razon_social = forms.CharField(label="Razon social o nombre", max_length=150)
    tipo_persona = forms.ChoiceField(
        label="Tipo de persona", choices=Cliente.TipoPersona.choices
    )
    giro = forms.CharField(label="Giro", max_length=150, required=False)

    username = forms.CharField(label="Nombre de acceso", max_length=60)
    email = forms.EmailField(label="Correo electronico", max_length=150)
    password1 = forms.CharField(label="Contrasena", widget=forms.PasswordInput)
    password2 = forms.CharField(
        label="Repita la contrasena", widget=forms.PasswordInput
    )

    def clean_rut(self):
        valor = self.cleaned_data["rut"]
        validar_rut(valor)
        rut = limpiar_rut(valor)
        if Cliente.objects.filter(rut=rut).exists():
            raise forms.ValidationError(
                "Ya existe un cliente con este RUT. Inicie sesion o contacte "
                "al area comercial."
            )
        return rut

    def clean_username(self):
        username = self.cleaned_data["username"]
        if Usuario.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Este nombre de acceso ya esta en uso.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Este correo ya esta registrado.")
        return email

    acepta_privacidad = forms.BooleanField(
        label="He leido y acepto la politica de privacidad y el tratamiento de mis datos "
              "personales",
        required=True,
        error_messages={"required": "Debe aceptar la politica de privacidad para registrarse."},
    )

    def clean(self):
        datos = super().clean()
        if datos.get("password1") != datos.get("password2"):
            self.add_error("password2", "Las contrasenas no coinciden.")
        if datos.get("password1") and len(datos["password1"]) < 10:
            self.add_error(
                "password1", "La contrasena debe tener al menos 10 caracteres."
            )
        return datos

    @transaction.atomic
    def guardar(self) -> Usuario:
        datos = self.cleaned_data
        cliente = Cliente.objects.create(
            rut=datos["rut"],
            razon_social=datos["razon_social"],
            tipo_persona=datos["tipo_persona"],
            giro=datos.get("giro", ""),
        )
        usuario = Usuario.objects.create_user(
            username=datos["username"],
            email=datos["email"],
            password=datos["password1"],
            cliente=cliente,
            es_interno=False,
        )
        # Evidencia del consentimiento (RNF-17, Ley 19.628 y Ley 21.719)
        from apps.seguridad.models import Auditoria

        Auditoria.objects.create(
            usuario=usuario, entidad="consentimiento", id_registro=str(usuario.pk),
            accion=Auditoria.Accion.CREACION, valor_anterior=None,
            valor_nuevo={"politica_privacidad": VERSION_POLITICA, "aceptada": True},
            origen=Auditoria.Origen.WEB,
        )
        return usuario


class SolicitudPresupuestoForm(BootstrapMixin, forms.ModelForm):
    """
    Solicitud de presupuesto (CU-COM-01).

    Los campos de especificacion tecnica se construyen dinamicamente a partir
    de parametro_tecnico: agregar un parametro no requiere tocar este
    formulario (RF-CAT-03, RF-ADM-04).
    """

    class Meta:
        model = SolicitudPresupuesto
        fields = ["modelo", "cantidad", "fecha_deseada", "direccion"]
        widgets = {
            "fecha_deseada": forms.DateInput(attrs={"type": "date"}),
        }
        labels = {
            "modelo": "Modelo de referencia",
            "cantidad": "Unidades requeridas",
            "fecha_deseada": "Fecha de entrega deseada",
            "direccion": "Direccion de instalacion",
        }

    def __init__(self, *args, cliente=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cliente = cliente

        self.fields["modelo"].queryset = ModeloProducto.objects.filter(
            publicado=True, activo=True
        )
        self.fields["modelo"].required = False
        self.fields["modelo"].empty_label = "Sin modelo de referencia"

        from apps.configuracion.parametros import max_unidades_solicitud

        self.fields["cantidad"].widget.attrs.update({"min": 1, "max": max_unidades_solicitud()})

        if cliente is not None:
            self.fields["direccion"].queryset = DireccionCliente.objects.filter(
                cliente=cliente
            )
        self.fields["direccion"].required = False

        # Especificacion tecnica dinamica
        self.parametros = list(ParametroTecnico.objects.prefetch_related("valores"))
        for parametro in self.parametros:
            nombre = f"param_{parametro.id_parametro}"
            etiqueta = parametro.etiqueta

            if parametro.tipo_dato == ParametroTecnico.TipoDato.LISTA:
                opciones = [("", "Seleccione")] + [
                    (v.valor, v.valor) for v in parametro.valores.filter(activo=True)
                ]
                campo = forms.ChoiceField(
                    label=etiqueta,
                    choices=opciones,
                    required=parametro.obligatorio,
                    widget=forms.Select(attrs={"class": "form-select"}),
                )
            elif parametro.tipo_dato == ParametroTecnico.TipoDato.NUMERICO:
                atributos = {"class": "form-control", "step": "any"}
                ayuda = ""
                if parametro.valor_minimo is not None:
                    atributos["min"] = parametro.valor_minimo.normalize()
                if parametro.valor_maximo is not None:
                    atributos["max"] = parametro.valor_maximo.normalize()
                if parametro.valor_minimo is not None and parametro.valor_maximo is not None:
                    ayuda = (f"Entre {parametro.valor_minimo.normalize():f} y "
                             f"{parametro.valor_maximo.normalize():f} {parametro.unidad}").strip()
                campo = forms.DecimalField(
                    label=etiqueta,
                    required=parametro.obligatorio,
                    help_text=ayuda,
                    widget=forms.NumberInput(attrs=atributos),
                )
            else:
                campo = forms.CharField(
                    label=etiqueta,
                    required=parametro.obligatorio,
                    widget=forms.TextInput(attrs={"class": "form-control"}),
                )
            self.fields[nombre] = campo

    def clean_cantidad(self):
        from apps.comercial.services import validar_cantidad

        cantidad = self.cleaned_data.get("cantidad")
        error = validar_cantidad(cantidad)
        if error:
            raise forms.ValidationError(error)
        return cantidad

    def clean(self):
        """Rangos tecnicos y valores que fija el modelo elegido (hallazgo H-01)."""
        from apps.comercial.services import validar_especificacion

        datos = super().clean()
        modelo = datos.get("modelo")
        for parametro in self.parametros:
            campo = f"param_{parametro.id_parametro}"
            valor = datos.get(campo)
            if valor in (None, "") or campo in self.errors:
                continue
            error = validar_especificacion(modelo, parametro, valor)
            if error:
                self.add_error(campo, error)
        return datos

    def campos_especificacion(self):
        """Devuelve solo los campos tecnicos, para renderizarlos aparte."""
        for parametro in self.parametros:
            yield parametro, self[f"param_{parametro.id_parametro}"]

    def especificaciones_ingresadas(self):
        for parametro in self.parametros:
            valor = self.cleaned_data.get(f"param_{parametro.id_parametro}")
            if valor not in (None, ""):
                yield parametro, str(valor)


class RecuperarClaveForm(BootstrapMixin, PasswordResetForm):
    """
    Recuperacion de clave (RF-SEG-05). El correo sale por el mismo canal que
    el resto de las notificaciones (Brevo), respetando CORREO_REDIRIGIR_A.
    No se copia a CORREO_COPIA_A: el enlace da acceso a la cuenta.
    """

    email = forms.EmailField(label="Correo registrado", max_length=150)

    def get_users(self, email):
        # Solo cuentas activas: una cuenta suspendida no recupera su acceso aqui
        return [u for u in super().get_users(email) if u.puede_ingresar]

    def send_mail(self, subject_template_name, email_template_name, context,
                  from_email, to_email, html_email_template_name=None):
        from apps.configuracion.services.notificaciones import enviar, url_sitio

        enlace = url_sitio("web:clave_nueva", context["uid"], context["token"])
        enviar("recuperar_clave", "SITRAFO: recuperacion de contrasena", [to_email],
               {"usuario": context["user"], "enlace": enlace, "url": enlace}, copia=False)


class NuevaClaveForm(BootstrapMixin, SetPasswordForm):
    pass


class DireccionForm(BootstrapMixin, forms.ModelForm):
    """Direcciones de la cuenta del cliente (RF-CLI-04)."""

    class Meta:
        model = DireccionCliente
        fields = ["tipo", "comuna", "calle", "numero"]
        labels = {"tipo": "Tipo de direccion", "calle": "Calle", "numero": "Numero"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["comuna"].queryset = self.fields["comuna"].queryset.select_related(
            "region").order_by("region__nombre", "nombre")
        self.fields["comuna"].label_from_instance = (
            lambda c: f"{c.nombre} ({c.region.nombre})")


class EmpresaForm(BootstrapMixin, forms.ModelForm):
    """
    Datos de la empresa editables por el cliente (RF-CLI-04, CU-CLI-07). El RUT
    y el tipo de persona no se cambian: identifican al cliente y sus documentos.
    """

    email = forms.EmailField(label="Correo de la cuenta", max_length=150)

    class Meta:
        model = Cliente
        fields = ["razon_social", "nombre_fantasia", "giro"]
        labels = {"razon_social": "Razon social o nombre",
                  "nombre_fantasia": "Nombre de fantasia", "giro": "Giro"}

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario
        self.fields["email"].initial = usuario.email if usuario else ""
        self.order_fields(["razon_social", "nombre_fantasia", "giro", "email"])

    def clean_email(self):
        correo = self.cleaned_data["email"].strip().lower()
        if Usuario.objects.filter(email__iexact=correo).exclude(pk=self.usuario.pk).exists():
            raise forms.ValidationError("Ese correo ya esta en uso por otra cuenta.")
        return correo


class CambiarClaveForm(BootstrapMixin, PasswordChangeForm):
    """Cambio de contrasena del cliente desde Mi cuenta (CU-CLI-07)."""

    error_messages = {
        **PasswordChangeForm.error_messages,
        "password_incorrect": "La contrasena actual no es correcta.",
        "password_mismatch": "Las contrasenas nuevas no coinciden.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo, etiqueta in (("old_password", "Contrasena actual"),
                                ("new_password1", "Contrasena nueva"),
                                ("new_password2", "Repita la contrasena nueva")):
            self.fields[campo].label = etiqueta
            self.fields[campo].help_text = ""
