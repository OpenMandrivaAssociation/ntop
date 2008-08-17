%define _disable_ld_no_undefined 1

%define name ntop
%define fname ntop

%define ntop_gid 120
%define ntop_uid 120
%define ntop_group ntop
%define ntop_user  ntop

Summary:	Network and traffic analyzer
Name:		%{name}
Version:	3.3.7
Release:	%mkrel 1
License:	GPLv3
Group:		Monitoring
URL:		http://www.ntop.org
Source0:	http://downloads.sourceforge.net/ntop/%{fname}-%{version}.tar.gz
Source1:	%{name}.init
Source2:	%{name}.logrotate
Source3:	http://standards.ieee.org/regauth/oui/oui.txt
Patch0:		ntop-path_to_dot.diff
Patch1:		ntop-automake_fixes.diff
Patch2:		ntop-mysql_headers.diff
Patch3:		ntop-no_usr_local_fix.diff
Requires(pre): rpm-helper
Requires(preun): rpm-helper
Requires(post): rpm-helper
Requires(postun): rpm-helper
Requires:	tcp_wrappers
Requires:	rrdtool
BuildRequires:	autoconf2.5
BuildRequires:	automake1.7
BuildRequires:	chrpath
BuildRequires:	gdbm-devel
BuildRequires:	gd-devel
BuildRequires:	gdome2-devel
BuildRequires:	glib2-devel
BuildRequires:	libjpeg-devel
BuildRequires:	libpcap-devel
BuildRequires:	libpng-devel
BuildRequires:	libtool
BuildRequires:  mysql-devel
BuildRequires:	ncurses-devel
BuildRequires:	net-snmp-devel >= 5.4.1-3
BuildRequires:	openssl-devel
BuildRequires:	pkgconfig
BuildRequires:	readline-devel
BuildRequires:  rpm-devel
BuildRequires:	rrdtool-devel
BuildRequires:	tcp_wrappers-devel
BuildRequires:	xpm-devel
BuildRequires:	zlib-devel
BuildRoot:	%{_tmppath}/%{fname}-%{version}-root

%define _requires_exceptions devel(.*)

%description
Ntop is a network and traffic analyzer that provides a wealth of information on
various networking hosts and protocols. ntop is primarily accessed via a
built-in web interface. Optionally, data may be stored into a database for
analysis or extracted from the web server in formats suitable for manipulation
in perl or php.

%prep

%setup -q
%patch0 -p0 -b .dot
%patch1 -p0 -b .automake_fixes
%patch2 -p1 -b .mysql_headers
%patch3 -p0 -b .no_usr_local_fix

# update oui.txt
rm -f oui.txt*
cp %{SOURCE3} oui.txt; gzip -9 oui.txt

%build
#cp -f acinclude.m4.ntop acinclude.m4
#libtoolize --copy --force; aclocal-1.7; autoconf; automake-1.7 --add-missing --copy

sh ./autogen.sh

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

make

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
find %{buildroot}%{_datadir}/%{fname}/html -type f -print0|xargs -0 chmod 644
find %{buildroot}%{_datadir}/%{fname}/html -type d -print0|xargs -0 chmod 755

# nuke rpath
chrpath -d %{buildroot}%{_libdir}/ntop/plugins/*.so

cat > README.urpmi << EOF
There are some manual steps you need to do, first start %{_sbindir}/ntop to set
the admin password, please consilte the docs/1STRUN.txt file for more info. After
that change directory to %{_sysconfdir}/ntop and execute the makecert.sh script to
generate the ntop-cert.pem file.

Have fun!
EOF

%pre
/usr/sbin/groupadd -g %{ntop_gid} -r %{ntop_group} 2>/dev/null || :
/usr/sbin/useradd -M -s /bin/false \
	-d /var/lib/%{name} \
	-c "system user for ntop" \
	-g %{ntop_group} -r -u %{ntop_uid} %{ntop_user} 2>/dev/null || :

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
%dir %{_datadir}/%{fname}
%{_datadir}/%{fname}/*
%{_libdir}/lib*
%dir %{_libdir}/%{name}
%{_libdir}/%{name}/*
%dir %{_sysconfdir}/ntop
%{_sysconfdir}/ntop/*
%attr(0711,%{ntop_user},%{ntop_group}) %dir /var/log/ntop
%attr(0711,%{ntop_user},%{ntop_group}) %dir /var/lib/ntop
