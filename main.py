import os
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, ListProperty, NumericProperty, ObjectProperty


class LoginScreen(Screen):
    def on_login(self):
        username = self.ids.input_user.text
        password = self.ids.input_pass.text
        App.get_running_app().login(username, password)

    def on_volver(self):
        App.get_running_app().root.current = "welcome"


class WelcomeScreen(Screen):
    logo_source = StringProperty("img/logo.png")

    def on_start(self):
        App.get_running_app().root.current = "login"


class MenuScreen(Screen):
    bienvenida_text = StringProperty("")

    def on_categoria(self, categoria):
        app = App.get_running_app()
        app.categoria_actual = categoria
        app.root.current = "catalogo"

    def on_carrito(self):
        App.get_running_app().root.current = "carrito"

    def on_logout(self):
        app = App.get_running_app()
        app.usuario = ""
        app.carrito = []
        app.categoria_actual = ""
        # Limpiar cajas de texto de LoginScreen
        login_screen = app.root.get_screen("login")
        if hasattr(login_screen.ids, "input_user"):
            login_screen.ids.input_user.text = ""
        if hasattr(login_screen.ids, "input_pass"):
            login_screen.ids.input_pass.text = ""
        app.root.current = "login"


class CatalogScreen(Screen):
    container = ObjectProperty(None)
    search_text = StringProperty("")

    def on_pre_enter(self):
        self.search_text = ""
        # Limpiar la caja de búsqueda si existe
        if hasattr(self.ids, "search_bar"):
            self.ids.search_bar.text = ""
        self.mostrar_productos()

    def on_search(self, texto):
        self.search_text = texto
        self.mostrar_productos()

    def mostrar_productos(self):
        self.container.clear_widgets()
        import os, json
        BASE_DIR = os.path.dirname(__file__)
        PRODUCTOS_FILE = os.path.join(BASE_DIR, "productos.json")
        try:
            with open(PRODUCTOS_FILE, "r", encoding="utf-8") as f:
                productos = json.load(f)
        except Exception as e:
            productos = []
            from kivy.uix.label import Label
            self.container.add_widget(Label(text=f"Error cargando productos: {e}", size_hint_y=None, height=40))
        app = App.get_running_app()
        categoria = getattr(app, "categoria_actual", None)
        productos_categoria = [p for p in productos if p.get("categoria", "") == categoria] if categoria else productos
        # Filtrar por búsqueda
        texto = self.search_text.lower().strip()
        if texto:
            productos_categoria = [p for p in productos_categoria if texto in p.get("nombre", "").lower() or texto in p.get("descripcion", "").lower()]
        from kivy.factory import Factory
        if not productos_categoria:
            from kivy.uix.label import Label
            self.container.add_widget(Label(text="No hay productos en esta categoría.", size_hint_y=None, height=40))
        else:
            for p in productos_categoria:
                item = Factory.ProductItem()
                item.nombre = p.get("nombre", "")
                item.descripcion = p.get("descripcion", "")
                item.precio = p.get("precio", 0)
                img_path = os.path.join("img", p.get("imagen", ""))
                item.img_path = img_path if os.path.exists(img_path) else ""
                self.container.add_widget(item)

    def on_volver(self):
        App.get_running_app().root.current = "menu"


class CarritoScreen(Screen):
    container = ObjectProperty(None)

    def on_pre_enter(self):
        self.container.clear_widgets()
        app = App.get_running_app()
        if not app.carrito:
            from kivy.uix.label import Label
            self.container.add_widget(Label(text="El carrito está vacío.", size_hint_y=None, height=40, color=(0,0,0,1)))
        else:
            total_final = 0
            for idx, producto in enumerate(app.carrito, 1):
                nombre = producto.get("nombre", "")
                cantidad = producto.get("cantidad", 1)
                precio = producto.get("precio", 0)
                subtotal = cantidad * precio
                total_final += subtotal
                from kivy.uix.label import Label
                self.container.add_widget(Label(text=str(idx), size_hint_y=None, height=40, color=(0,0,0,1)))
                self.container.add_widget(Label(text=nombre, size_hint_y=None, height=40, color=(0,0,0,1)))
                self.container.add_widget(Label(text=str(cantidad), size_hint_y=None, height=40, color=(0,0,0,1)))
                self.container.add_widget(Label(text=f"${subtotal:.2f}", size_hint_y=None, height=40, color=(0,0,0,1)))
                self.container.add_widget(Label(text="", size_hint_y=None, height=40, color=(0,0,0,0)))
            # Fila de total final
            for _ in range(3):
                self.container.add_widget(Label(text="", size_hint_y=None, height=40, color=(0,0,0,0)))
            self.container.add_widget(Label(text="TOTAL", bold=True, size_hint_y=None, height=40, color=(0,0,0,1)))
            self.container.add_widget(Label(text=f"${total_final:.2f}", bold=True, size_hint_y=None, height=40, color=(0,0,0,1)))

    def on_volver(self):
        App.get_running_app().root.current = "menu"

    def on_imprimir_ticket(self):
        app = App.get_running_app()
        if not app.carrito:
            app.mostrar_popup("Error", "El carrito está vacío.")
            return
        import datetime
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        import webbrowser
        fecha = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        nombre = f"ticket_{app.usuario}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        TICKET_DIR = os.path.join(os.path.dirname(__file__), "tickets")
        os.makedirs(TICKET_DIR, exist_ok=True)
        ruta = os.path.join(TICKET_DIR, nombre)
        total = sum([item.get('cantidad', 1) * item.get('precio', 0) for item in app.carrito])
        cliente = getattr(app, 'usuario', 'Cliente')
        c = canvas.Canvas(ruta, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 750, "CATÁLOGO MAZAHUA - TICKET")
        c.setFont("Helvetica", 12)
        c.drawString(50, 730, f"Fecha: {fecha}")
        c.drawString(50, 710, f"Cliente: {cliente}")
        c.line(50, 705, 550, 705)
        c.drawString(50, 690, "Producto")
        c.drawString(250, 690, "Cantidad")
        c.drawString(350, 690, "Subtotal")
        c.line(50, 685, 550, 685)
        y = 670
        for item in app.carrito:
            nombre_prod = item.get('nombre', '')
            cantidad = item.get('cantidad', 1)
            precio = item.get('precio', 0)
            subtotal = cantidad * precio
            c.drawString(50, y, nombre_prod)
            c.drawString(250, y, str(cantidad))
            c.drawString(350, y, f"${subtotal:.2f}")
            y -= 20
        c.line(50, y, 550, y)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y-20, f"TOTAL: ${total:.2f}")
        c.setFont("Helvetica", 12)
        c.drawString(50, y-50, "¡Gracias por tu compra!")
        c.save()
        webbrowser.open(ruta)


class CatalogoMazahuaApp(App):
    usuario = StringProperty("")
    carrito = ListProperty([])
    categoria_actual = StringProperty("")

    def build(self):
        self.title = "Catálogo Digital Mazahua"
        return Builder.load_file("mazahua.kv")

    def login(self, username, password):
        # Solo permite usuario 'CECYTEM' y password '1234', sin importar mayúsculas/minúsculas y espacios
        # Solo permite usuario 'CECYTEM' y password '1234', sin importar mayúsculas/minúsculas y espacios
        if username.strip().lower() == "cecytem" and password.strip() == "1234":
            self.usuario = "CECYTEM"
            self.root.current = "menu"
            menu = self.root.get_screen("menu")
            menu.bienvenida_text = f"Bienvenid@, {self.usuario}"
        else:
            self.mostrar_popup("Error", "Usuario o contraseña incorrectos.")

    def agregar_al_carrito(self, producto):
        # Si el producto ya está en el carrito, suma la cantidad
        for item in self.carrito:
            if item.get("nombre") == producto.get("nombre"):
                item["cantidad"] = item.get("cantidad", 1) + 1
                self.mostrar_popup("Agregado al carrito", f"{producto.get('nombre', '')} agregado al carrito.")
                return
        # Si no está, lo agrega con cantidad 1
        producto["cantidad"] = 1
        self.carrito.append(producto)
        self.mostrar_popup("Agregado al carrito", f"{producto.get('nombre', '')} agregado al carrito.")

    def mostrar_popup(self, titulo, mensaje):
        from kivy.uix.popup import Popup
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label
        import threading

        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=mensaje))
        popup = Popup(title=titulo, content=content, size_hint=(None,None), size=(300,200))
        popup.open()
        # Cerrar automáticamente después de 1.5 segundos
        def cerrar():
            import time
            time.sleep(1.5)
            if popup.parent:
                popup.dismiss()
        threading.Thread(target=cerrar, daemon=True).start()


if __name__ == "__main__":
    CatalogoMazahuaApp().run()
