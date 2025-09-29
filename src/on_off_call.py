from on_off_class import ParentOnOff 

on_off = ParentOnOff("/dev/gpiochip0", 28, "out")
print("******************1")
on_off.start()
print("******************2")