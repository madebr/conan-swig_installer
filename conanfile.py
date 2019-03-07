# -*- coding: utf-8 -*-

from conans import ConanFile, tools, AutoToolsBuildEnvironment
from conans.util.env_reader import get_env
import os 
import shutil
import tempfile


class SwigConan(ConanFile):
    name = "swig_installer"
    version = "3.0.12"
    description = """SWIG is a software development tool that connects programs written
                     in C and C++ with a variety of high-level programming languages."""

    topics = ("conan", "swig", "python", "java", "wrapper")
    url = "https://github.com/ss1978/conan-swig.git"
    homepage = "http://www.swig.org"
    author = "bincrafters <bincrafters@gmail.com>"
    license = "GPL-3.0"
    exports = ["LICENSE.md"]
    settings = "os_build", "compiler", "arch_build"
    _source_subfolder = "sources"

    def _fetch_sources(self, target_folder):
        if self.settings.os_build == "Windows":
            filename = "{}win-{}.zip".format("swig", self.version)
            url = "http://prdownloads.sourceforge.net/swig/swigwin-{}.zip".format(self.version)
            sha256 = "21ce6cbe297a56b697ef6e7e92a83e75ca41dedc87e48282ab444591986c35f5"

            self._download_cache_rename(url, sha256, filename, target_folder, "swigwin-{}".format(self.version), self._source_subfolder)
        else:
            filename = "{}-rel-{}.tar.gz".format("swig", self.version)
            url = "https://github.com/swig/swig/archive/rel-{}.tar.gz".format(self.version)
            sha256 = "64971de92b8a1da0b9ffb4b51e9214bb936c4dbbc304367899cdb07280b94af6"

            self._download_cache_rename(url, sha256, filename, target_folder, "{}-rel-{}".format("swig", self.version), self._source_subfolder)

    def _download_cache_rename(self, url, sha256, filename, target_folder, rename_from, rename_to):
        dlfilepath = os.path.join(tempfile.gettempdir(), filename)
        if os.path.exists(dlfilepath) and not get_env("SWIG_INSTALLER_FORCE_DOWNLOAD", False):
            self.output.info("Skipping download. Using cached {}".format(dlfilepath))
        else:
            self.output.info("Downloading {} from {}".format(self.name, url))
            tools.download(url, dlfilepath)
        tools.check_sha256(dlfilepath, sha256)
        tools.untargz(dlfilepath, destination=target_folder)
        os.rename(os.path.join(target_folder, rename_from), os.path.join(target_folder, rename_to))

    def build_requirements(self):
        if tools.os_info.is_windows:
            self.build_requires("msys2_installer/latest@bincrafters/stable")
        if self.settings.os_build != "Windows":
            self.build_requires("pcre/8.41@bincrafters/stable")
            if tools.os_info.is_windows:
                pass
            else:
                self.build_requires("bison_installer/3.3.2@bincrafters/stable")
                # self.build_requires("bison/3.3.2@bincrafters/stable")

    def system_requirements(self):
        if self.develop:
            if tools.os_info.with_yum:
                installer = tools.SystemPackageTool()
                packages = [
                    "autoconf",
                    "automake",
                ]
                for package in packages:
                    installer.install(package)


    def build(self):
        self._fetch_sources(self.build_folder)
        if self.settings.os_build == "Windows":
            pass
        else:
            env_build = AutoToolsBuildEnvironment(self)
            with tools.chdir(os.path.join(self.build_folder, self._source_subfolder)):
                self.run('./autogen.sh')
            args = [
                "PCRE_LIBS={}".format(" ".join("-l{}".format(lib) for lib in self.deps_cpp_info["pcre"].libs)),
                "PCRE_CPPFLAGS={}".format(""),
            ]
            env_build.configure(configure_dir=os.path.join(self.build_folder, self._source_subfolder), args=args)
            env_build.make()

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        if self.settings.os_build == "Windows":
            self.copy("swig.exe", )
            if not os.path.exists(os.path.join(self.build_folder,"bin", "swig.exe")):
                os.makedirs(os.path.join(self.build_folder,"bin"))
                shutil.copyfile(os.path.join(self._source_subfolder,"swig.exe"), os.path.join(self.build_folder, "bin", "swig.exe"))
                os.makedirs(os.path.join(self.build_folder,"share","swig"))
                shutil.copytree(os.path.join(self._source_subfolder,"Lib"), os.path.join(self.build_folder, "share", "swig", self.version))
        else:
            with tools.chdir(self.build_folder):
                env_build = AutoToolsBuildEnvironment(self)
                env_build.install()
                with tools.chdir(os.path.join(self.package_folder, "bin")):
                    self.run("strip swig")
                    self.run("strip ccache-swig")

    def package_id(self):
        del self.info.settings.compiler

    def package_info(self):
        bindir = os.path.join(self.package_folder, "bin")
        self.output.info('Appending PATH environment variable: {}'.format(bindir))
        self.env_info.PATH.append(bindir)

        swig_lib_path = os.path.join(self.package_folder, "share", "swig", self.version)
        self.output.info('Appending SWIG_LIB environment variable: {}'.format(swig_lib_path))
        self.env_info.SWIG_LIB = swig_lib_path

        self.output.info('Setting SWIG_INSTALLER_ROOT to {}'.format(self.package_folder))
        self.env_info.SWIG_INSTALLER_ROOT = self.package_folder
