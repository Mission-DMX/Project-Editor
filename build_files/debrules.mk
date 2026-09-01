#!/usr/bin/make -f
# -*- makefile -*-

export DH_VERBOSE = 1

%:
	# Let debhelper run the default sequence
	# (installdeb, installmime, installdocs, …)
	dh $@

override_dh_auto_install:
	# First let the standard dh_auto_install copy the built files
	dh_auto_install

	# Let debhelper run the mime‑handling helper (updates‑mime‑database)
	dh_installmime

	# Install any additional documentation (optional)
	dh_installdocs
