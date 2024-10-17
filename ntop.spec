%define _requires_exceptions devel(.*)
%define _provides_exceptions devel(.*)
%define _disable_ld_no_undefined 1

Name:		ntop
Version:	5.0.1
Release:	2
Summary:	Network and traffic analyzer
License:	GPLv2
Group:		Monitoring
URL:		https://www.ntop.org
Source0:	http://downloads.sourceforge.net/ntop/%{name}-%{version}.tar.gz
Source2:	%{name}.logrotate
Source3:	http://standards.ieee.org/regauth/oui/oui.txt
Source4:	%{name}.conf
Source5:	%{name}.service
Patch0:		ntop-dot-default-path.patch
Patch5:		ntop-4.0-system_lua.patch
Patch6:		ntop-running-user.patch
Patch7:		ntop-5.0.1-automake-1.13.patch
BuildRequires:	gdbm-devel
BuildRequires:	gd-devel
BuildRequires:	GeoIP-devel
BuildRequires:	pkgconfig(glib-2.0)
BuildRequires:	pkgconfig(libevent)
BuildRequires:	jpeg-devel
BuildRequires:	pcap-devel
BuildRequires:	pcre-devel
BuildRequires:	pkgconfig(libpng)
BuildRequires:	libtool
BuildRequires:	lua-devel >= 5.1.4
BuildRequires:  mysql-devel
BuildRequires:  perl-devel
BuildRequires:  python-devel
BuildRequires:	ncurses-devel
BuildRequires:	net-snmp-devel >= 5.4.1-3
BuildRequires:	openssl-devel
BuildRequires:	pkgconfig
BuildRequires:	readline-devel
BuildRequires:	rrdtool-devel
BuildRequires:	tcp_wrappers-devel
BuildRequires:	xpm-devel
BuildRequires:	zlib-devel
BuildRequires:	wget
BuildRequires:	subversion

Requires(post):  rpm-helper >= 0.24.8-1
Requires(preun): rpm-helper >= 0.24.8-1
Requires:	tcp_wrappers
Requires:	rrdtool
Requires:	geoip

%description
Ntop is a network and traffic analyzer that provides a wealth of information on
various networking hosts and protocols. ntop is primarily accessed via a
built-in web interface. Optionally, data may be stored into a database for
analysis or extracted from the web server in formats suitable for manipulation
in perl or php.

%prep
%setup -q
%patch0 -p0 -b .dot
%patch5 -p1 -b .system_lua
%patch6 -p0 -b .default-user-to-ntop
%patch7 -p1 -b .automake-1_13
# update oui.txt
rm -f oui.txt*
cp %{SOURCE3} oui.txt; gzip -9 oui.txt

%build
sh ./autogen.sh --noconfig

%serverbuild

%configure2_5x \
    --disable-static \
    --bindir=%{_sbindir} \
    --localstatedir=/var/lib \
    --enable-snmp

%make

%install
rm -rf %{buildroot}

%makeinstall_std

install -d %{buildroot}%{_localstatedir}/lib/%{name}/rrd/{flows,graphics,interfaces}

#Create folder for archive logs
install -d %{buildroot}%{_localstatedir}/log/%{name}

chmod 644 %{buildroot}%{_sysconfdir}/%{name}/*gz

install -D -m 0644 %{SOURCE5} %{buildroot}%{_unitdir}/%{name}.service
install -D -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
install -D -m 0644 %{SOURCE4} %{buildroot}%{_sysconfdir}/%{name}.conf

# cleanup
rm -rf %{buildroot}%{_libdir}/*.{a,la}
rm -rf %{buildroot}%{_libdir}/plugins
rm -rf %{buildroot}%{_sysconfdir}/%{name}/%{name}-cert.pem

# fix permissions
find %{buildroot}%{_datadir}/%{name}/html -type f -print0|xargs -0 chmod 644
find %{buildroot}%{_datadir}/%{name}/html -type d -print0|xargs -0 chmod 755

cat > README.urpmi << EOF
There are some manual steps you need to do, first start %{_sbindir}/%{name} to
set the admin password, please check %_datadir/doc/%name/1STRUN.txt file for
more info. 
EOF

%pre
%_pre_useradd %{name} %{_localstatedir}/lib/%{name} /bin/false

%post
%_post_service ntop
%_create_ssl_certificate ntop -b

%preun
%_preun_service ntop

%files
%doc AUTHORS CONTENTS COPYING ChangeLog NEWS PORTING MANIFESTO SUPPORT_NTOP.txt
%doc THANKS docs/FAQ docs/HACKING docs/KNOWN_BUGS docs/FILES docs/README
%doc docs/1STRUN.txt docs/database NetFlow README.urpmi
%{_sysconfdir}/logrotate.d/ntop
%config(noreplace) %{_sysconfdir}/ntop.conf
%{_sysconfdir}/ntop/*.gz
%{_sysconfdir}/ntop/*.dat
%{_unitdir}/ntop.service
%{_sbindir}/%{name}
%{_mandir}/man8/%{name}.8.*
%{_datadir}/%{name}/
%{_libdir}/libnetflowPlugin.so
%{_libdir}/libntop.so
%{_libdir}/libntopreport.so
%{_libdir}/librrdPlugin.so
%{_libdir}/libsflowPlugin.so
%{_libdir}/libnetflowPlugin-%{version}.so
%{_libdir}/libntop-%{version}.so
%{_libdir}/libntopreport-%{version}.so
%{_libdir}/librrdPlugin-%{version}.so
%{_libdir}/libsflowPlugin-%{version}.so
%{_libdir}/%{name}/
%attr(-,ntop,ntop) %{_localstatedir}/lib/ntop
%attr(-,ntop,ntop) %{_localstatedir}/log/ntop
