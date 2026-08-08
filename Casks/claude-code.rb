cask "claude-code" do
  arch arm: "arm64", intel: "x64"
  os macos: "darwin", linux: "linux"

  version "2.1.225"
  sha256 arm:          "08d6e85dd2b80883bb8da93cbeae3dc79b4704d6b84a05d614bf1ff4a5155b69",
         x86_64:       "0065d7155f83a3a5b0e0153ca3b70ad902b33dc06747c8b4e4d0bad58c6e0ec5",
         x86_64_linux: "0a3be8d18cb0f5357d38ce2d588601753a60b44cc9c622579ed8b8405dee231e",
         arm64_linux:  "209d4279c0a3dbb48bee6017d99430269ec6aba59cd8735b1fda0f9664139a45"

  url "https://downloads.claude.ai/claude-code-releases/#{version}/#{os}-#{arch}/claude",
      verified: "downloads.claude.ai/claude-code-releases/"
  name "Claude Code"
  desc "Terminal-based AI coding assistant"
  homepage "https://claude.com/product/claude-code"

  livecheck do
    url "https://downloads.claude.ai/claude-code-releases/latest"
    regex(/^v?(\d+(?:\.\d+)+)$/i)
  end

  binary "claude"

  zap trash: [
        "~/.cache/claude",
        "~/.claude.json*",
        "~/.config/claude",
        "~/.local/bin/claude",
        "~/.local/share/claude",
        "~/.local/state/claude",
        "~/Library/Caches/claude-cli-nodejs",
      ],
      rmdir: "~/.claude"
end
