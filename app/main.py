import tkinter as tk
from tkinter import messagebox

from app.render_manager import RenderManager
from app.ui import JazanApp


def main():
    render_manager = RenderManager()
    status = render_manager.get_service_status()

    if status.get("status") == "not_configured":
        root = tk.Tk()
        root.withdraw()
        result = messagebox.askyesno(
            "Render غير مهيأ",
            "لم يتم إدخال بيانات Render بعد. هل تريد فتح التطبيق محليًا؟\n\nملاحظة: سيتم تشغيل التطبيق بدون فحص Render الحالي.",
        )
        root.destroy()

        if not result:
            return

    elif not status.get("can_start"):
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Render غير مفعّل",
            status.get("message", "Render غير مفعّل حاليًا. قم بتفعيل الخدمة ثم أعد تشغيل التطبيق."),
        )
        root.destroy()
        return

    app = JazanApp()
    app.mainloop()


if __name__ == "__main__":
    main()
