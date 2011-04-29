%define _requires_exceptions devel(.*)
%define _provides_exceptions devel(.*)
%define _disable_ld_no_undefined 1

Name:		ntop
Version:	4.0.3
Release:	%mkrel 1
Summary:	Network and traffic analyzer
License:	GPLv3
Group:		Monitoring
URL:		http://www.ntop.org
Source0:	http://downloads.sourceforge.net/ntop/%{name}-%{version}.tar.gz
Source1:	%{name}.init
Source2:	%{name}.logrotate
Source3:	http://standards.ieee.org/regauth/oui/oui.txt
Patch0:		ntop-path_to_dot.diff
Patch2:		ntop-mysql_headers.diff
Patch3:		ntop-no_usr_local_fix.diff
Patch4:		ntop-4.0-system_geoip.patch
Patch5:		ntop-4.0-system_lua.patch
Requires(pre): rpm-helper
Requires(preun): rpm-helper
Requires(post): rpm-helper
Requires(postun): rpm-helper
Requires:	tcp_wrappers
Requires:	rrdtool
Requires:	geoip
BuildRequires:	chrpath
BuildRequires:	gdbm-devel
BuildRequires:	gd-devel
BuildRequires:	gdome2-devel
BuildRequires:	GeoIP-devel
BuildRequires:	glib2-devel
BuildRequires:	libevent-devel
BuildRequires:	libjpeg-devel
BuildRequires:	libpcap-devel
BuildRequires:	libpcre-devel
BuildRequires:	libpng-devel
BuildRequires:	libtool
BuildRequires:	lua-devel >= 5.1.4
BuildRequires:  mysql-devel
BuildRequires:  perl-devel
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
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

%description
Ntop is a network and traffic analyzer that provides a wealth of information on
various networking hosts and protocols. ntop is primarily accessed via a
built-in web interface. Optionally, data may be stored into a database for
analysis or extracted from the web server in formats suitable for manipulation
in perl or php.

%prep

%setup -q
%patch0 -p0 -b .dot
%patch2 -p1 -b .mysql_headers
%patch3 -p0 -b .no_usr_local_fix
%patch4 -p1 -b .system_geoip
%patch5 -p1 -b .system_lua

# update oui.txt
rm -f oui.txt*
cp %{SOURCE3} oui.txt; gzip -9 oui.txt

%build
sh ./autogen.sh --noconfig

%serverbuild

# populate CPPFLAGS with some includes
export CPPFLAGS="$CPPFLAGS `pkg-config --cflags-only-I gdome2` `pkg-config --cflags-only-I glib-2.0`"
export CORELIBS="$CORELIBS `mysql_config --libs_r` -ldl -lm -lwrap"

%configure2_5x \
    --bindir=%{_sbindir} \
    --disable-static \
    --enable-optimize \
    --enable-tcpwrap \
    --enable-sslv3 \
    --enable-snmp \
    --sysconfdir=%{_sysconfdir} \
    --mandir=%{_mandir} \
    --with-localedir=%{_datadir}/locale \
    --localstatedir=/var/lib

cat >> config.h <<EOF
#define HAVE_LIBDL 1
#define HAVE_LIBM 1
#define HAVE_LIBMYSQLCLIENT_R 1
#define HAVE_LIBWRAP 1
#define HAVE_MYSQL_H 1
EOF

#rpath problem
sed -i \
    -e 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' \
    -e 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' \
    libtool

%make

%install
rm -rf %{buildroot}

install -d %{buildroot}%{_sysconfdir}/{logrotate.d,sysconfig}
install -d %{buildroot}%{_initrddir}
install -d %{buildroot}/var/log/ntop

%makeinstall_std

chmod 644 %{buildroot}%{_sysconfdir}/ntop/*gz
rm -f %{buildroot}%{_sysconfdir}/ntop/ntop-cert.pem

cat > %{buildroot}%{_sysconfdir}/ntop/makecert.sh <<EOF
#!/bin/sh
openssl req -new -x509 -sha1 -extensions v3_ca -nodes -days 1825 -out cert.pem
cat privkey.pem cert.pem > ntop-cert.pem
rm -f privkey.pem cert.pem
chmod 600 ntop-cert.pem
EOF

chmod 755 %{buildroot}%{_sysconfdir}/ntop/makecert.sh

install -m0755 %{SOURCE1} %{buildroot}%{_initrddir}/ntop
install -m0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/logrotate.d/ntop

cat > %{buildroot}%{_sysconfdir}/sysconfig/%{name} <<EOF
# In this file, you can specify extra argument passed
# to ntop daemon at startup.
# Notice -u (user), -P (data dir) and -d (run as daemon)
# are allready set in init script
extra_arg=""

EOF

# cleanup
#rm -rf %{buildroot}%{_prefix}/lib%{name}
rm -rf %{buildroot}%{_libdir}/*.{a,la}
rm -rf %{buildroot}%{_libdir}/plugins

# fix permissions
find %{buildroot}%{_datadir}/%{name}/html -type f -print0|xargs -0 chmod 644
find %{buildroot}%{_datadir}/%{name}/html -type d -print0|xargs -0 chmod 755

# nuke rpath
#chrpath -d %{buildroot}%{_libdir}/ntop/plugins/*.so

cat > README.urpmi << EOF
There are some manual steps you need to do, first start %{_sbindir}/ntop to set
the admin password, please consilte the docs/1STRUN.txt file for more info. After
that change directory to %{_sysconfdir}/ntop and execute the makecert.sh script to
generate the ntop-cert.pem file.

Have fun!
EOF

%pre
%_pre_useradd %{name} %{_localstatedir}/lib/%{name} /bin/false

%post
%if %mdkversion < 200900
/sbin/ldconfig
%endif
%_post_service ntop

%preun
%_preun_service ntop

%if %mdkversion < 200900
%postun -p /sbin/ldconfig
%endif

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
%doc AUTHORS CONTENTS COPYING ChangeLog NEWS PORTING MANIFESTO SUPPORT_NTOP.txt
%doc THANKS docs/FAQ docs/HACKING docs/KNOWN_BUGS docs/FILES docs/README
%doc docs/1STRUN.txt docs/database NetFlow README.urpmi
%{_sysconfdir}/logrotate.d/ntop
%config(noreplace) %{_sysconfdir}/sysconfig/%name
%{_initrddir}/ntop
%{_sbindir}/*
%{_mandir}/*/*
%dir %{_datadir}/%{name}
%{_datadir}/%{name}/*
%{_libdir}/lib*
%dir %{_libdir}/%{name}
%{_libdir}/%{name}/*
%dir %{_sysconfdir}/ntop
%{_sysconfdir}/ntop/*
%attr(0711,ntop,ntop) %dir /var/log/ntop
%attr(0711,ntop,ntop) %dir /var/lib/ntop
