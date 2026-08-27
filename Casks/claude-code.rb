cask "claude-code" do
  arch arm: "arm64", intel: "x64"
  os macos: "darwin", linux: "linux"

  version "2.1.247"
  sha256 arm:          "5086b9b64d8bb842e1f599cdd3767ab08c6b2266e462fcc5686ae4b019cca8f7",
         x86_64:       "162e65d7bf8735dbcdc75b0122dbb126d5704a00e682bbdfc413749188a20cfd",
         x86_64_linux: "5fb321bf417ffc5cd4e3f36e7c9c7e029bf47aaa36d5621db979fcc5e6eabe15",
         arm64_linux:  "a68bb633f85e4a0e73465952ea624cf18992c3fa4db615feeb942ffad57d082a"

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
