Name:           trackora
Version:        1.0.0
Release:        1%{?dist}
Summary:        Privacy-focused activity and screen time tracker for GNOME Wayland

License:        MIT
URL:            https://github.com/SamXop123/Trackora
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros
BuildRequires:  python3-setuptools
BuildRequires:  python3-wheel
BuildRequires:  desktop-file-utils
BuildRequires:  libappstream-glib

Requires:       gnome-shell >= 45
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description
Trackora is a privacy-focused activity and screen time tracker designed for GNOME Shell on Fedora Wayland.
It features an active window detector extension, a SQLite-backed backend service, and a premium PySide6 dashboard interface.

%prep
%autosetup -n %{name}-%{version}

%generate_buildrequires
%pyproject_buildrequires

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files trackora

# Install systemd user service
install -m 0644 -D systemd/trackora.service %{buildroot}%{_userunitdir}/trackora.service

# Install desktop entry
install -m 0644 -D trackora/assets/trackora.desktop %{buildroot}%{_datadir}/applications/trackora.desktop

# Install AppStream metadata
install -m 0644 -D trackora/assets/trackora.metainfo.xml %{buildroot}%{_metainfodir}/trackora.metainfo.xml

# Install GNOME shell extension
mkdir -p %{buildroot}%{_datadir}/gnome-shell/extensions/trackora@trackora.dev
cp -rp shell-extension/trackora@trackora.dev/* %{buildroot}%{_datadir}/gnome-shell/extensions/trackora@trackora.dev/

# Install the app icon
install -m 0644 -D trackora/assets/trackora_logo.png %{buildroot}%{_datadir}/pixmaps/trackora.png

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/trackora.desktop
appstream-util validate-relax --nonet %{buildroot}%{_metainfodir}/trackora.metainfo.xml

%post
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
%systemd_user_post trackora.service

%preun
%systemd_user_preun trackora.service

%postun
if [ $1 -eq 0 ] ; then
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
fi
%systemd_user_postun_with_restart trackora.service

%files -f %{pyproject_files}
%doc README.md DEVELOPMENT.md CHANGELOG.md
%license LICENSE
%{_bindir}/trackora-gui
%{_bindir}/trackora-daemon
%{_userunitdir}/trackora.service
%{_datadir}/applications/trackora.desktop
%{_metainfodir}/trackora.metainfo.xml
%{_datadir}/gnome-shell/extensions/trackora@trackora.dev/
%{_datadir}/pixmaps/trackora.png

%changelog
* Tue Jul 07 2026 SamXop123 <dot_notsam> - 1.0.0-1
- Official stable v1.0 release.

* Mon Jun 29 2026 SamXop123 <dot_notsam> - 1.0.0rc1-1
- Release Candidate 1 with full packaging polish and fixes.

* Sun Jun 28 2026 SamXop123 <dot_notsam> - 1.0.0b1-1
- Initial release for public beta.
