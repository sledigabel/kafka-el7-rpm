%define __jar_repack 0
%define debug_package %{nil}
%define _prefix      /opt
%define _conf_dir    %{_sysconfdir}/kafka
%define _log_dir     %{_var}/log/kafka
%define _data_dir    %{_sharedstatedir}/kafka

Summary: Apache Kafka is publish-subscribe messaging rethought as a distributed commit log.
Name: kafka
Version: %{version}
Release: %{build_number}
License: Apache License, Version 2.0
Group: Applications
URL: http://kafka.apache.org/
Source0: %{source}
Source1: kafka.service
Source2: kafka.logrotate
Source3: server.properties
Source4: log4j.properties
Source5: kafka.sysconfig
%if %{build_with_metrics}
# adding metric specific sources.
Source6: metrics-graphite-2.2.0.jar
Source7: kafka-graphite-1.0.0.jar
%endif
BuildRoot: %{_tmppath}/%{name}-%{version}-root
Prefix: %{_prefix}
Vendor: Apache Software Foundation
Packager: Ivan Dyachkov <ivan.dyachkov@klarna.com>
Provides: kafka kafka-server
BuildRequires: systemd
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description
Kafka is designed to allow a single cluster to serve as the central data backbone for a large organization. It can be elastically and transparently expanded without downtime. Data streams are partitioned and spread over a cluster of machines to allow data streams larger than the capability of any single machine and to allow clusters of co-ordinated consumers. Messages are persisted on disk and replicated within the cluster to prevent data loss.

%prep
%setup -n %{source_name}

%build
rm -f libs/{*-javadoc.jar,*-scaladoc.jar,*-sources.jar,*-test.jar}

%install
mkdir -p $RPM_BUILD_ROOT%{_prefix}/kafka/{libs,bin,config}
mkdir -p $RPM_BUILD_ROOT%{_log_dir}
mkdir -p $RPM_BUILD_ROOT%{_data_dir}
mkdir -p $RPM_BUILD_ROOT%{_unitdir}/kafka.service.d
mkdir -p $RPM_BUILD_ROOT%{_conf_dir}/
install -p -D -m 755 bin/*.sh $RPM_BUILD_ROOT%{_prefix}/kafka/bin
install -p -D -m 644 config/* $RPM_BUILD_ROOT%{_prefix}/kafka/config
install -p -D -m 755 %{S:1} $RPM_BUILD_ROOT%{_unitdir}/
install -p -D -m 644 %{S:2} $RPM_BUILD_ROOT%{_sysconfdir}/logrotate.d/kafka
install -p -D -m 644 %{S:3} $RPM_BUILD_ROOT%{_conf_dir}/
install -p -D -m 644 %{S:4} $RPM_BUILD_ROOT%{_conf_dir}/
install -p -D -m 644 %{S:5} $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/kafka
install -p -D -m 644 libs/* $RPM_BUILD_ROOT%{_prefix}/kafka/libs
%if %{build_with_metrics}
# adding metric specific sources.
install -p -D -m 644 %{S:6} $RPM_BUILD_ROOT%{_prefix}/kafka/libs
install -p -D -m 644 %{S:7} $RPM_BUILD_ROOT%{_prefix}/kafka/libs
%endif
# stupid systemd fails to expand file paths in runtime
CLASSPATH=
for f in $RPM_BUILD_ROOT%{_prefix}/kafka/libs/*.jar
do
  CLASSPATH="%{_prefix}/kafka/libs/$(basename ${f}):${CLASSPATH}"
done
echo "[Service]" > $RPM_BUILD_ROOT%{_unitdir}/kafka.service.d/classpath.conf
echo "Environment=CLASSPATH=${CLASSPATH}" >> $RPM_BUILD_ROOT%{_unitdir}/kafka.service.d/classpath.conf

%clean
rm -rf $RPM_BUILD_ROOT

%pre
/usr/bin/getent group kafka >/dev/null || /usr/sbin/groupadd -r kafka
if ! /usr/bin/getent passwd kafka >/dev/null ; then
    /usr/sbin/useradd -r -g kafka -m -d %{_prefix}/kafka -s /bin/bash -c "Kafka" kafka
fi

%post
%systemd_post kafka.service

%preun
%systemd_preun kafka.service

%postun
# When the last version of a package is erased, $1 is 0
# Otherwise it's an upgrade and we need to restart the service
if [ $1 -ge 1 ]; then
    /usr/bin/systemctl restart kafka.service
fi
/usr/bin/systemctl daemon-reload >/dev/null 2>&1 || :

%files
%defattr(-,root,root)
%{_unitdir}/kafka.service
%{_unitdir}/kafka.service.d/classpath.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/kafka
%config(noreplace) %{_sysconfdir}/sysconfig/kafka
%config(noreplace) %{_conf_dir}/*
%attr(-,kafka,kafka) %{_prefix}/kafka
%attr(0755,kafka,kafka) %dir %{_log_dir}
%attr(0700,kafka,kafka) %dir %{_data_dir}
%doc NOTICE
%doc LICENSE
