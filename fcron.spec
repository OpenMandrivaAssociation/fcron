Summary:	Task scheduler
Name:		fcron
Version:	3.3.3
Release:	1
License:	GPLv2+
Group:		System/Configuration/Other
URL:		https://fcron.free.fr/
Source0:	http://fcron.free.fr/archives/%{name}-%{version}.src.tar.gz
BuildRequires:	pam-devel
BuildRequires:	sendmail-command
BuildRequires:	neovim
BuildRequires:	systemd
Requires:	syslog-daemon
Requires:	sendmail-command
Provides:	cron-daemon
BuildConflicts:	libselinux-devel

%patchlist
fcron-3.0.5-Makefile.in.diff

%description
Fcron is a scheduler. It aims at replacing Vixie Cron, so it implements most
of its functionalities.

But contrary to Vixie Cron, fcron does not need your system to be up 7 days
a week, 24 hours a day : it also works well with systems which are
not running neither all the time nor regularly (contrary to anacrontab).

In other words, fcron does both the job of Vixie Cron and anacron, but does
even more and better :)) ...

%files
%{_initrddir}/fcron
%attr(640,root,fcron) %config(noreplace) %{_sysconfdir}/fcron.conf
%attr(640,root,fcron) %config(noreplace) %{_sysconfdir}/fcron.allow
%attr(640,root,fcron) %config(noreplace) %{_sysconfdir}/fcron.deny
%config(noreplace) %{_sysconfdir}/pam.d/fcron
%config(noreplace) %{_sysconfdir}/pam.d/fcrontab
%{_tmpfilesdir}/%{name}.conf
%{_mandir}/man8/fcron.8*
%{_mandir}/man1/fcrontab.1*
%{_mandir}/man1/fcrondyn.1*
%{_mandir}/man1/fcron-update-crontabs.1*
%{_mandir}/man5/fcrontab.5*
%{_mandir}/man5/fcron.conf.5*
%{_mandir}/man3/bitstring.3*
%lang(fr) %{_mandir}/fr/man?/*
%attr(6111,root,root) %{_bindir}/convert-fcrontab
%attr(6111,root,root) %{_bindir}/fcronsighup
%attr(6111,root,root) %{_bindir}/fcrondyn
%attr(6111,fcron,fcron) %{_bindir}/fcrontab
%attr(110,root,root) %{_sbindir}/fcron
%{_sbindir}/fcron-update-crontabs
%dir %attr(770,fcron,fcron) /var/spool/fcron
%{_unitdir}/*.service
%{_sysusersdir}/*.conf

#----------------------------------------------------------------------------

%prep
%setup -q -T -b 0 -n %{name}-%{version}
%autopatch -p1

%build
%configure \
	--with-sendmail=/bin/false \
	--with-shell=/bin/sh \
	--with-editor=/bin/vi \
	--with-etcdir=%{_sysconfdir} \
	--with-spooldir=/var/spool/fcron \
	--with-run-non-privileged=no \
	--with-username=fcron \
	--with-groupname=fcron \
	--with-sysfcrontab=yes \
	--with-pam=yes \
	--with-selinux=no

perl -pi \
	-e 's|^#define SENDMAIL .*|#define SENDMAIL "%{_libdir}/sendmail"|;' \
	-e 's|^#define PIDFILE .*|#define PIDFILE "/run/fcron/fcron.pid"|;' \
	-e 's|^#define FIFOFILE .*|#define FIFOFILE "/run/fcron/fcron.fifo"|;' \
	config.h

%make OPTIM="%{optflags} -I%{_includedir}/selinux"

%install
install -d %{buildroot}%{_docdir}
install -d %{buildroot}%{_sysconfdir}/pam.d
install -d %{buildroot}%{_bindir}
install -d %{buildroot}%{_sbindir}
install -d %{buildroot}%{_mandir}/man{1,3,5,8}
install -d %{buildroot}%{_initrddir}
install -d %{buildroot}/var/spool/fcron

yes n | make install \
	DESTDIR=%{buildroot} \
	ROOTNAME=`id -un` ROOTGROUP=`id -gn`

install -m 755 script/sysVinit-launcher %{buildroot}%{_initrddir}/fcron
install -m 755 convert-fcrontab %{buildroot}%{_bindir}

install -m755 debian/fcron-update-crontabs %{buildroot}%{_sbindir}/
install -m644 debian/fcron-update-crontabs.1 %{buildroot}%{_mandir}/man1/

install -m644 files/fcron.pam %{buildroot}%{_sysconfdir}/pam.d/fcron
install -m644 files/fcrontab.pam %{buildroot}%{_sysconfdir}/pam.d/fcrontab

# fixup
perl -pi \
	-e 's|SBIN=@\@DESTSBIN@|SBIN=%{_sbindir}|;' \
	-e 's|^# pidfile: .*|# pidfile: /run/fcron/fcron.pid|;' \
	%{buildroot}%{_initrddir}/fcron
perl -pi \
	-e "s|^pidfile.*|pidfile = /run/fcron/fcron\.pid|;" \
	-e "s|^fifofile.*|fifofile = /run/fcron/fcron\.fifo|;" \
	%{buildroot}%{_sysconfdir}/fcron.conf

# nuke installed files
rm -rf %{buildroot}%{_docdir}/%{name}-%{version}
rm -f %{buildroot}%{_sysconfdir}/pam.conf

# nuke permissions (for strip)
chmod 755 %{buildroot}%{_bindir}/*
chmod 755 %{buildroot}%{_sbindir}/*

mkdir -p %{buildroot}%{_tmpfilesdir}
cat <<EOF > %{buildroot}%{_tmpfilesdir}/%{name}.conf
d /run/fcron 0755 root root
EOF

mkdir -p %{buildroot}%{_sysusersdir}
cat >%{buildroot}%{_sysusersdir}/%{name}.conf <<EOF
u fcron - "FCron" /var/spool/fcron %{_sbindir}/nologin
EOF
