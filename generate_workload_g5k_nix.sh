sudo-g5k

sudo mkdir -p /nix/var/nix/profiles/per-user/$USER
sudo chown -R $USER /nix

curl -L https://nixos.org/nix/install | bash

. ~/.nix-profile/etc/profile.d/nix.sh

nix-shell pyshell.nix --run "bash script_generate_workload.sh"