[app]
title = StegKivy
package.name = stegkivy
package.domain = org.stegkivy
source.dir = src
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

requirements = python3==3.10,\
    kivy==2.3.0,\
    pillow==10.4.0,\
    stegano==0.11.4,\
    plyer==2.1.0,\
    cryptography==44.0.0,\
    exifread==3.0.0,\
    scipy==1.14.1,\
    py7zr==0.22.0,\
    kivymd==2.0.0

android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.accept_sdk_license = True

# (str) Presplash of the application
presplash.filename = %(source.dir)s/assets/presplash.png

# (str) Icon of the application
icon.filename = %(source.dir)s/assets/icon.png

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
android.gradle_dependencies = org.xerial:sqlite-jdbc:3.36.0
android.add_aars = libs/*.aar
android.add_jars = libs/*.jar

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash background color (for android toolchain)
android.presplash_color = #000000

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 33

# (bool) If True, then skip trying to update the Android sdk
# This can be useful to avoid excess Internet downloads or save time
# when an update is due and you just want to test/build your package
android.skip_update = False 