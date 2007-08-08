%define name ntop
%define fname ntop

%define ntop_gid 120
%define ntop_uid 120
%define ntop_group ntop
%define ntop_user  ntop

Summary:	Network and traffic analyzer
Name:		%{name}
Version:	3.2
Release:	%mkrel 11
License:	GPL
Group:		Monitoring
URL:		http://www.ntop.org
Source0:	%{fname}-%{version}.tar.bz2
Source1:	%{name}.init
Source2:	%{name}.logrotate
Patch0:		%{name}-%{version}-gcc32.patch
Patch1:		%{name}-%{version}-dot.patch
Requires(pre): rpm-helper
Requires(preun): rpm-helper
Requires(post): rpm-helper
Requires(postun): rpm-helper
BuildRequires:	libpcap-devel
BuildRequires:	ncurses-devel
BuildRequires:	readline-devel
BuildRequires:	tcp_wrappers-devel
BuildRequires:	gdbm-devel
BuildRequires:	openssl-devel
BuildRequires:	libjpeg-devel
BuildRequires:	libpng-devel
BuildRequires:	xpm-devel
BuildRequires:	zlib-devel
BuildRequires:	gdome2-devel
BuildRequires:	gd-devel
BuildRequires:	net-snmp-devel
BuildRequires:	pkgconfig
BuildRequires:	chrpath
BuildRequires:  rpm-devel
%if %{mdkversion} == 1000
BuildRequires:	autoconf2.5
BuildRequires:	automake1.7
%endif
BuildRoot:	%{_tmppath}/%{fname}-%{version}-root

%define _requires_exceptions devel(.*)

%description
Ntop is a network and traffic analyzer that provides a wealth of
information on various networking hosts and protocols. ntop is
primarily accessed via a built-in web interface. Optionally, data may
be stored into a database for analysis or extracted from the web
server in formats suitable for manipulation in perl or php.

%prep
%setup -q
%if %{mdkversion} == 1000
%patch0 -p1 -b .gcc32
%endif
%patch1 -p1 -b .dot

%build

# populate CPPFLAGS with some includes
export CPPFLAGS="$CPPFLAGS `pkg-config --cflags-only-I gdome2` `pkg-config --cflags-only-I glib-2.0`"

%if %{mdkversion} == 1000
aclocal-1.7
autoconf-2.5x
automake-1.7 ||

CFLAGS="%{optflags}"
export CFLAGS
CXXFLAGS="%{optflags}"
export CXXFLAGS
./configure	%{_target_platform} \
		--bindir=%{_sbindir} \
		--enable-optimize \
		--enable-tcpwrap \
		--enable-sslv3 \
		--enable-snmp \
		--sysconfdir=%{_sysconfdir} \
		--mandir=%{_mandir} \
		--program-prefix= \
		--localstatedir=%{_localstatedir} \
		--datadir=%{_datadir} \
		--with-localedir=%{_datadir}/locale \
		--prefix=%{_prefix}
%else
%configure	--bindir=%{_sbindir} \
		--enable-optimize \
		--enable-tcpwrap \
		--enable-sslv3 \
		--enable-snmp \
		--sysconfdir=%{_sysconfdir} \
		--mandir=%{_mandir} \
		--with-localedir=%{_datadir}/locale \
		--localstatedir=%{_localstatedir}

%endif

%make

%install
rm -rf %{buildroot}

install -d %{buildroot}%{_sysconfdir}/{logrotate.d,sysconfig}
install -d %{buildroot}%{_initrddir}
install -d %{buildroot}%{_datadir}/snmp/mibs
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

# install the mib file
install -m0644 plugins/NTOP-MIB.txt %{buildroot}%{_datadir}/snmp/mibs/NTOP-MIB.txt

# cleanup
#rm -rf %{buildroot}%{_prefix}/lib%{name}
rm -rf %{buildroot}%{_libdir}/*.{a,la}
rm -rf %{buildroot}%{_libdir}/plugins

# fix permissions
find %{buildroot}%{_datadir}/%{fname}/html -type f -print0|xargs -0 chmod 644
find %{buildroot}%{_datadir}/%{fname}/html -type d -print0|xargs -0 chmod 755

# nuke rpath
chrpath -d %{buildroot}%{_libdir}/ntop/plugins/*.so

%pre
/usr/sbin/groupadd -g %{ntop_gid} -r %{ntop_group} 2>/dev/null || :
/usr/sbin/useradd -M -s /bin/false \
	-d %{_localstatedir}/%{name} \
	-c "system user for ntop" \
	-g %{ntop_group} -r -u %{ntop_uid} %{ntop_user} 2>/dev/null || :

%post
/sbin/ldconfig
%_post_service ntop

%preun
%_preun_service ntop

%postun -p /sbin/ldconfig

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
%doc AUTHORS CONTENTS COPYING ChangeLog NEWS PORTING MANIFESTO SUPPORT_NTOP.txt
%doc THANKS docs/FAQ docs/HACKING docs/KNOWN_BUGS docs/FILES docs/README
%doc docs/1STRUN.txt plugins/README.SNMP www
%config %{_sysconfdir}/logrotate.d/ntop
%config(noreplace) %{_sysconfdir}/sysconfig/%name
%config %{_initrddir}/ntop
%{_sbindir}/*
%{_mandir}/*/*
%dir %{_datadir}/%{fname}
%{_datadir}/%{fname}/*
%{_libdir}/lib*
%dir %{_libdir}/%{name}
%{_libdir}/%{name}/*
%dir %{_sysconfdir}/ntop
%{_sysconfdir}/ntop/*
%{_datadir}/snmp/mibs/NTOP-MIB.txt
%attr(0711,%{ntop_user},%{ntop_group}) %dir /var/log/ntop
%attr(0710,%{ntop_user},%{ntop_group}) %dir %{_localstatedir}/ntop

