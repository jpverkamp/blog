---
title: Wombat IDE - Ant build script
date: 2011-09-11 04:55:00
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
I've been having issues with the automatic updates and half-manually building things through Eclipse, so I decided to use a build system. Previously, the only experience I have with such systems is <a title="GNU make homepage" href="http://www.gnu.org/software/make/manual/make.html">GNU make</a> which isn't particularly Java specific. So I decided to learn something new and try out <a title="Apache Ant Homepage" href="http://ant.apache.org/">Apache ANT</a>as a build system. Essentially, I've added the following features:

* `revision` - get the [SVN](http://subversion.apache.org/ "Apache Subversion") revision number to use as the current version
* `compile` - compile the code (required `revision`)
* `dist` - create a {{< wikipedia page="JAR (file format)" text="JAR" >}} file from the built code (requires `compile`)
* `sign` - sign the JAR files so they can be deployed (requires `dist`)
* `deploy` - create the files necessary for [Webstart](http://www.oracle.com/technetwork/java/javase/tech/index-jsp-136112.html "Java Webstart Homepage") (requires `dist`, `sign`, and `revision`)


<!--more-->

You can see the entire file in the <a title="Wombat IDE Source Code" href="https://code.google.com/p/wombat-ide/source/checkout">repository</a>, but there are a few interesting bits that I'll share here. First, there is the `revision` target which runs svn and uses the output from that to grab the revision:

```xml
<target name="revision" description="initialize things">
	<exec executable="svn" output="${build-dir}/svn.properties">
		<arg value="info" />
	</exec>
	<property prefix="svn" file="${build-dir}/svn.properties"/>
	<property name="revision" value="${svn.Revision}" />
	<property name="jar-name" value="Wombat-${revision}.jar" />
	<echo>Current version: ${revision}</echo>
</target>
```

Second, that code is then used to automatically insert the version number into the source code so that it can always be displayed in the title bar of the GUI (this helps with debugging, allowing students to instantly tell if they have an old version):

```xml
<copy file="${src-dir}/wombat/Wombat.java" tofile="${src-dir}/wombat/Wombat.java.bak" />
<replace file="${src-dir}/wombat/Wombat.java" token="{REVISION}" value="${revision}" />

<copy todir="${build-dir}">
	<fileset dir="${src-dir}" />
</copy>
<javac srcdir="${src-dir}" destdir="${build-dir}" classpathref="classpath" />

<move file="${src-dir}/wombat/Wombat.java.bak" tofile="${src-dir}/wombat/Wombat.java" />
</target>
```

Finally, the deploy code:

```xml
<target name="deploy" depends="dist,sign,revision" description="deploy to webstart">
	<tstamp>
		<format property="date" pattern="d MMMM yyyy" />
	</tstamp>

	<copy todir="${dist-dir}">
		<fileset dir="${jnlp-dir}" />
	</copy>

	<replace dir="${dist-dir}" includes="*.html *.jnlp *.txt" token="{DATE}" value="${date}" />
	<replace dir="${dist-dir}" includes="*.html *.jnlp *.txt" token="{REVISION}" value="${revision}" />

	<input message="Password:" addproperty="scp-passphrase">
	      <handler classname="org.apache.tools.ant.input.SecureInputHandler" />
	</input>

	<sshexec host="${deploy-server}" username="${deploy-user}" keyfile="${user.home}/.ssh/id_dsa" passphrase="${scp-passphrase}" trust="yes" command="rm -f ${deploy-dir}/Wombat-*.jar" failonerror="false" />

	<scp todir="${deploy-user}@${deploy-server}:${deploy-dir}" keyfile="${user.home}/.ssh/id_dsa" passphrase="${scp-passphrase}" trust="yes">
		<fileset dir="${dist-dir}" />
	</scp>

	<sshexec host="${deploy-server}" username="${deploy-user}" keyfile="${user.home}/.ssh/id_dsa" passphrase="${scp-passphrase}" trust="yes" command="chmod 755 ${deploy-dir}" />
	<sshexec host="${deploy-server}" username="${deploy-user}" keyfile="${user.home}/.ssh/id_dsa" passphrase="${scp-passphrase}" trust="yes" command="chmod 664 ${deploy-dir}/*" />
</target>
```

Basically, it asks for your password once and then uses that to remove the old versions from the server then upload and set permissions on the new version, all completely without any intervention from the user beyond that password. I can't even say how much time this has already saved me, but I'm willing to bet that it will more than make up for the time I spent leaning Ant.