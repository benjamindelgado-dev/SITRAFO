"""Formularios de la aplicacion web del cliente."""
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction

from apps.catalogo.models import ModeloProducto, ParametroTecnico
from apps.clientes.models import Cliente, Comuna, DireccionCliente
from apps.common.validators import limpiar_rut, validar_rut
from apps.comercial.models import SolicitudPresupuesto
from apps.seguridad.models import Usuario


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
        return Usuario.objects.create_user(
            username=datos["username"],
            email=datos["email"],
            password=datos["password1"],
            cliente=cliente,
            es_interno=False,
        )


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

        if cliente is not None:
            self.fields["direccion"].queryset = DireccionCliente.objects.filter(
                cliente=cliente
            )
        self.fields["direccion"].required = False

        # Especificacion tecnica dinamica
        self.parametros = list(ParametroTecnico.objects.prefetch_related("valores"))
        for parametro in self.parametros:
            nombre = f"param_{parametro.id_parametro}"
            etiqueta = f"{parametro.nombre} ({parametro.unidad})"

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
                campo = forms.DecimalField(
                    label=etiqueta,
                    required=parametro.obligatorio,
                    widget=forms.NumberInput(attrs={"class": "form-control"}),
                )
            else:
                campo = forms.CharField(
                    label=etiqueta,
                    required=parametro.obligatorio,
                    widget=forms.TextInput(attrs={"class": "form-control"}),
                )
            self.fields[nombre] = campo

    def campos_especificacion(self):
        """Devuelve solo los campos tecnicos, para renderizarlos aparte."""
        for parametro in self.parametros:
            yield parametro, self[f"param_{parametro.id_parametro}"]

    def especificaciones_ingresadas(self):
        for parametro in self.parametros:
            valor = self.cleaned_data.get(f"param_{parametro.id_parametro}")
            if valor not in (None, ""):
                yield parametro, str(valor)
