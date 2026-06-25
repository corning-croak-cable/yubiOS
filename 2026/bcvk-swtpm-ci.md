# bcvk swtpm CI
Add swtpm to bcvk test VM + enable systemd-tpm2-swtpm.service so CI VMs satisfy ConditionSecurity=measured-os and cover TPM2 code paths.
Primary changes in yubi-OS/bcvk; this branch tracks yubiOS CI workflow integration.