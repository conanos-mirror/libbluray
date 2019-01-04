from conans import ConanFile, tools, MSBuild
from conanos.build import config_scheme
import os, shutil


class LibblurayConan(ConanFile):
    name = "libbluray"
    version = "1.0.2-3"
    description = "libbluray is an open-source library designed for Blu-Ray Discs playback for media players "
    url = "https://github.com/conanos/libbluray"
    homepage = "https://www.videolan.org/developers/libbluray.html"
    license = "LGPL"
    generators = "visual_studio", "gcc"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = { 'shared': True, 'fPIC': True }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx

        config_scheme(self)

    def requirements(self):
        self.requires.add("fontconfig/2.13.0@conanos/stable")
        self.requires.add("libxml2/2.9.8@conanos/stable")
        self.requires.add("libiconv/1.15@conanos/stable")

    def source(self):
        url_ = 'https://github.com/ShiftMediaProject/libbluray/archive/{version}.tar.gz'
        tools.get(url_.format(version=self.version))
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def build(self):
        if self.settings.os == 'Windows':
            with tools.chdir(os.path.join(self._source_subfolder,"SMP")):
                for proj in ["libbluray.vcxproj"]:
                    tools.replace_in_file(proj, "iconvd.lib","iconv.lib",strict=False)
                    tools.replace_in_file(proj, "xml2d.lib","libxml2.lib",strict=False)
                    tools.replace_in_file(proj, "fontconfigd.lib","fontconfig.lib",strict=False)

                msbuild = MSBuild(self)
                build_type = str(self.settings.build_type) + ("DLL" if self.options.shared else "")
                msbuild.build("libbluray.sln",upgrade_project=True,platforms={'x86': 'Win32', 'x86_64': 'x64'},build_type=build_type)

    def package(self):
        if self.settings.os == 'Windows':
            platforms={'x86': 'Win32', 'x86_64': 'x64'}
            rplatform = platforms.get(str(self.settings.arch))
            self.copy("*", dst=os.path.join(self.package_folder,"include"), src=os.path.join(self.build_folder,"..", "msvc","include"))
            if self.options.shared:
                for i in ["lib","bin"]:
                    self.copy("*", dst=os.path.join(self.package_folder,i), src=os.path.join(self.build_folder,"..","msvc",i,rplatform))
            self.copy("*", dst=os.path.join(self.package_folder,"licenses"), src=os.path.join(self.build_folder,"..", "msvc","licenses"))

            tools.mkdir(os.path.join(self.package_folder,"lib","pkgconfig"))
            shutil.copyfile(os.path.join(self.build_folder,self._source_subfolder,"src","libbluray.pc.in"),
                            os.path.join(self.package_folder,"lib","pkgconfig", "libbluray.pc"))
            lib = "-lblurayd" if self.options.shared else "-lbluray"
            replacements = {
                "@prefix@"             :    self.package_folder,
                "@exec_prefix@"        :    "${prefix}/bin",
                "@libdir@"             :    "${prefix}/lib",
                "@includedir@"         :    "${prefix}/include",
                "@PACKAGE_VERSION@"    :    self.version,
                "@DLOPEN_LIBS@"        :    "",
                "@FONTCONFIG_LIBS@"    :    "",
                "@PACKAGES@"           :    "",
                "-lbluray"             :    lib
            }
            for s, r in replacements.items():
                tools.replace_in_file(os.path.join(self.package_folder,"lib","pkgconfig", "libbluray.pc"),s,r)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

