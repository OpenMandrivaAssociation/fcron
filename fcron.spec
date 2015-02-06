Summary:	Task scheduler
Name:		fcron
Version:	3.0.6
Release:	2
License:	GPLv2+
Group:		System/Configuration/Other
URL:		http://fcron.free.fr/
Source0:	http://fcron.free.fr/archives/%{name}-%{version}.src.tar.gz
Source1:	%{name}-2.0.0-extra.tar.bz2
Patch0:		fcron-3.0.5-Makefile.in.diff
# (fc) 3.0.4-5mdv accept fcron.conf file with 644 perms (Fedora)
Patch1:		fcron-3.0.2-accept_readable_fcron.conf.patch
BuildRequires:	pam-devel
BuildRequires:	sendmail-command
BuildRequires:	vim-minimal
Requires(post):	systemd
Requires(pre,preun,post,postun):	rpm-helper
Requires:	syslog-daemon
Requires:	sendmail-command
Provides:	cron-daemon
BuildConflicts:	libselinux-devel

%description
Fcron is a scheduler. It aims at replacing Vixie Cron, so it implements most
of its functionalities.

But contrary to Vixie Cron, fcron does not need your system to be up 7 days
a week, 24 hours a day : it also works well with systems which are
not running neither all the time nor regularly (contrary to anacrontab).

In other words, fcron does both the job of Vixie Cron and anacron, but does
even more and better :)) ...

%files
%doc fcrontab.example
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

%pre
# Check now if there is an old ( < 1.1.x ) version of fcrontab on the system.
echo `fcron -V 2>&1 | grep "^fcron "` > /tmp/PREVIOUS_VERSION
if [ "$1" = "1" ]; then
    %_pre_useradd fcron /var/spool/fcron /bin/true
fi

%post
%_tmpfilescreate %{name}
if [ "$1" = "2" ]; then
    killall -TERM fcron
    FCRONTABS=/var/spool/fcron

    find ${FCRONTABS} -type f \( -name "*.orig" -a ! -name "root.orig" \) \
        -exec chown fcron:fcron {} \; -exec chmod 640 {} \;
    find ${FCRONTABS} -type f -name "root.orig" -exec chown root:fcron {} \; -exec chmod 600 {} \;
    find ${FCRONTABS} -type f ! -name "*.orig" -exec chown root:root {} \; -exec chmod 600 {} \;
    [ -f %{_sysconfdir}/fcron.deny ] && chown root:fcron %{_sysconfdir}/fcron.deny
    [ -f %{_sysconfdir}/fcron.allow ] && chown root:fcron %{_sysconfdir}/fcron.allow

    if test -r "/tmp/PREVIOUS_VERSION"; then
        MAJOR=`cat /tmp/PREVIOUS_VERSION | awk '{print $2}' | awk -F '.' '{print $1}'`
        MINOR=`cat /tmp/PREVIOUS_VERSION | awk '{print $2}' | awk -F '.' '{print $2}'`
    fi

    if test \( "$MAJOR" -lt 1 \) -o \( \( "$MINOR" -lt 1 \) -a "$MAJOR" -eq 1 \); then
        for FILE in $FCRONTABS/* ; do \
            if test "$FILE" != "$FCRONTABS/*"; then
                BASENAME=`basename $FILE` ; \
                FCRONTAB=`echo "$BASENAME" | \
                sed "s|.*orig|| ; s|fcrontab.sig|| ; s|rm.*||"` ; \
                ( test ! -z "$FCRONTAB" && convert-fcrontab $FCRONTAB ) \
                || echo -n ""; \
            fi
        done
    fi
fi

%{_initrddir}/fcron start
%_post_service %{name}

%postun
if [ "$1" = "0" ]; then
    # Remove user fcron
    %_postun_userdel fcron
fi

%preun
%_preun_service %{name}


#----------------------------------------------------------------------------

%prep
%setup -q -T -b 0 -n %{name}-%{version} -a1
mv %{name}-2.0.0-extra/fcrontab.example ./

%patch0 -p0
%patch1 -p0 -b .readable-file

%build
%configure2_5x \
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

