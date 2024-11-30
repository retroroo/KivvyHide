[app]
title = StegKivy
package.name = stegkivy
package.domain = org.stegkivy
source.dir = src
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

requirements = python3,kivy==2.3.0,\
    pillow==10.4.0,\
    stegano==0.11.4,\
    plyer==2.1.0,\
    cryptography==44.0.0,\
    exifread==3.0.0,\
    scipy==1.14.1,\
    py7zr==0.22.0,\
    kivymd==2.0.0

android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,INTERNET
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
android.gradle_dependencies = org.xerial:sqlite-jdbc:3.36.0
android.add_aars = libs/*.aar
android.add_jars = libs/*.jar

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash background color (for android toolchain)
android.presplash_color = #000000

# (bool) If True, then skip trying to update the Android sdk
android.skip_update = False

# Python for Android specific
p4a.branch = develop
p4a.source_dir = 

# Force a specific Python version from python.org
p4a.bootstrap = sdl2
p4a.python_package = python3

# Add specific URLs for downloading
android.gradle_url = https://services.gradle.org/distributions/gradle-7.3-bin.zip
