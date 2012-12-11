%define _requires_exceptions devel(.*)
%define _provides_exceptions devel(.*)
%define _disable_ld_no_undefined 1

Name:		ntop
Version:	4.0.3
Release:	%mkrel 2
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


%changelog
* Mon Jul 18 2011 Oden Eriksson <oeriksson@mandriva.com> 4.0.3-2mdv2011
+ Revision: 690296
- rebuilt against new net-snmp libs

* Fri Apr 29 2011 Guillaume Rousse <guillomovitch@mandriva.org> 4.0.3-1
+ Revision: 660674
- new version

* Thu Mar 17 2011 Oden Eriksson <oeriksson@mandriva.com> 4.0-6
+ Revision: 645851
- relink against libmysqlclient.so.18

* Sat Jan 01 2011 Oden Eriksson <oeriksson@mandriva.com> 4.0-5mdv2011.0
+ Revision: 627269
- rebuilt against mysql-5.5.8 libs, again

* Thu Dec 30 2010 Oden Eriksson <oeriksson@mandriva.com> 4.0-4mdv2011.0
+ Revision: 626550
- rebuilt against mysql-5.5.8 libs

* Wed Dec 22 2010 Oden Eriksson <oeriksson@mandriva.com> 4.0-3mdv2011.0
+ Revision: 623876
- rebuilt against libevent 2.x

* Tue Oct 12 2010 Funda Wang <fwang@mandriva.org> 4.0-2mdv2011.0
+ Revision: 585070
- rebuild for new net-snmp

* Tue Jul 20 2010 Guillaume Rousse <guillomovitch@mandriva.org> 4.0-1mdv2011.0
+ Revision: 555130
- use standard rpm-helper macros for creating user, and don't hardcode uid/gid
- drop useless redundant macros
- drop useless patch and build dependencies
- new version

* Fri Apr 16 2010 Funda Wang <fwang@mandriva.org> 3.3.10-4mdv2010.1
+ Revision: 535275
- rpm-devel is not requried

* Thu Feb 18 2010 Oden Eriksson <oeriksson@mandriva.com> 3.3.10-3mdv2010.1
+ Revision: 507524
- rebuild

* Thu Oct 15 2009 Oden Eriksson <oeriksson@mandriva.com> 3.3.10-2mdv2010.0
+ Revision: 457694
- rebuild

* Wed Sep 09 2009 Oden Eriksson <oeriksson@mandriva.com> 3.3.10-1mdv2010.0
+ Revision: 435316
- fix deps
- 3.3.10 (fixes CVE-2009-2732)
- use system lua and geoip

* Sun Dec 07 2008 Funda Wang <fwang@mandriva.org> 3.3.8-3mdv2009.1
+ Revision: 311544
- rebuild for new mysql

* Wed Oct 29 2008 Oden Eriksson <oeriksson@mandriva.com> 3.3.8-2mdv2009.1
+ Revision: 298324
- rebuilt against libpcap-1.0.0

* Sat Oct 11 2008 Funda Wang <fwang@mandriva.org> 3.3.8-1mdv2009.1
+ Revision: 292192
- put back *.so as it will not introduce extra dependencies
- New version 3.3.8
- don't ship .so files as development linker

* Sun Aug 17 2008 Oden Eriksson <oeriksson@mandriva.com> 3.3.7-1mdv2009.0
+ Revision: 272911
- 3.3.7
- use _disable_ld_no_undefined due to ugly autopoo
- restore changes in the init script
- rediffed P0
- added P3 to avoid useless pollution during build
- new oui.txt file (S3)

  + Thierry Vignaud <tv@mandriva.org>
    - rebuild

  + Pixel <pixel@mandriva.com>
    - do not call ldconfig in %%post/%%postun, it is now handled by filetriggers
    - adapt to %%_localstatedir now being /var instead of /var/lib (#22312)

* Wed Mar 26 2008 Oden Eriksson <oeriksson@mandriva.com> 3.3-3mdv2008.1
+ Revision: 190305
- fix #25940 (warning request)
- don't start it per default

  + Olivier Blin <oblin@mandriva.com>
    - restore BuildRoot

  + Thierry Vignaud <tv@mandriva.org>
    - kill re-definition of %%buildroot on Pixel's request

* Mon Dec 17 2007 Oden Eriksson <oeriksson@mandriva.com> 3.3-2mdv2008.1
+ Revision: 121765
- added a fresh oui.txt file (S3)
- fix deps
- make the utterly borked autopoo stuff link correctly
- added mysql support
- activated net-snmp support again (thanks pld)

* Sat Aug 18 2007 Oden Eriksson <oeriksson@mandriva.com> 3.3-1mdv2008.0
+ Revision: 65597
- fix build, again...
- fix deps (rrdtool-devel)
- fix build
- 3.3
- drop obsolete patches
- rediffed the dot patch
- disable snmp support due to an unknown build error
- rebuilt against new net-snmp libs


* Mon Jan 09 2006 Oden Eriksson <oeriksson@mandriva.com> 3.2-10mdk
- rebuilt against new net-snmp libs with new major (10)

* Mon Jan 09 2006 Olivier Blin <oblin@mandriva.com> 3.2-9mdk
- fix typo in initscript

* Mon Jan 09 2006 Olivier Blin <oblin@mandriva.com> 3.2-8mdk
- convert parallel init to LSB
- fix typos in Requires(X)

* Wed Jan 04 2006 Oden Eriksson <oeriksson@mandriva.com> 3.2-7mdk
- rebuilt against new net-snmp with new major (10)

* Wed Jan 04 2006 Nicolas Lécureuil <neoclust@mandriva.org> 3.2-6mdk
- Add BuildRequires

* Mon Jan 02 2006 Olivier Blin <oblin@mandriva.com> 3.2-5mdk
- parallel init support

* Thu Dec 22 2005 Oden Eriksson <oeriksson@mandriva.com> 3.2-4mdk
- rebuilt against net-snmp that has new major (9)
- added some lib64 fixes
- added fixes here and there...

* Wed Dec 14 2005 Giuseppe Ghibò <ghibo@mandriva.com> 3.2-3mdk
- Added data files into /usr/libntop/ntop/*.

* Sun Nov 13 2005 Olivier Thauvin <nanardon@mandriva.org> 3.2-2mdk
- fix PreReq

* Sun Nov 13 2005 Olivier Thauvin <nanardon@mandriva.org> 3.2-1mdk
- 3.2

* Tue Sep 27 2005 Gwenole Beauchesne <gbeauchesne@mandriva.com> 3.1-3mdk
- fix buffer overflow (aka fortify fixes)

* Wed Jul 13 2005 Oden Eriksson <oeriksson@mandriva.com> 3.1-2mdk
- rebuilt against new libpcap-0.9.1 (aka. a "play safe" rebuild)

* Wed Feb 16 2005 Sylvie Terjan <erinmargault@mandrake.org> 3.1-1mdk
- 3.1-1mdk

* Tue Aug 10 2004 Olivier Thauvin <thauvin@aerov.jussieu.fr> 3.0-4mdk
- allow settings extra arg in /etc/sysconfig/ntop

* Fri Apr 23 2004 Olivier Blin <blino@mandrake.org> 3.0-3mdk
- keep .so files and use requires_exceptions for devel packages

* Wed Apr 21 2004 Olivier Blin <blino@mandrake.org> 3.0-2mdk
- remove .a and .la files as well
- merge previous changes and changelog entry
  (this package should be libified)

* Tue Apr 20 2004 Anne Nicolas <anne@lea-linux.org> 3.0-1mdk
- Version 3.0
- drop PO and P1
- remove E option in init script

* Sun Feb 01 2004 Michael Scherer <misc@mandrake.org> 2.2-3mdk
- fix Requires ( should not requires devel )

* Fri Sep 05 2003 Marcel Pol <mpol@gmx.net> 2.2-2mdk
- buildrequires

* Mon Jun 16 2003 Per Øyvind Karlsen <peroyvind@sintrax.net> 2.2-1mdk
- Version 2.2
- drop uterly useless Prefix tag
- drop P0
- use %%makeinstall_std macro
- remove unpackaged files
- buildrequires
- fix E: ntop no-prereq-on rpm-helper
- fix unowned dirs
- fix so that we don't include debug files

* Thu Feb 20 2003 Giuseppe Ghibò <ghibo@mandrakesoft.com> 2.1.3-1mdk
- Version 2.1.3.

