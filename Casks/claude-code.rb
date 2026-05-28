cask "claude-code" do
  arch arm: "arm64", intel: "x64"
  os macos: "darwin", linux: "linux"

  version "2.1.153"
  sha256 arm:          "449d9c89d7a63b1d427d912a7bd6e6f23f9a7b363866697c9fa9a0012546b254",
         x86_64:       "4b90521c64b728caabe221737ce8a83d362ef0852eee7d789f014f7ff73ce97b",
         arm64_linux:  "6277fbbea72228a069e4719fc3e5fa36f16749247a2321c520dae93e83e92d9c",
         x86_64_linux: "214f603f31942162dac9a65f18d43b3ac646ae215240fad481c4aad6c60f2e38"

  url "https://storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819/claude-code-releases/#{version}/#{os}-#{arch}/claude",
      verified: "storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819/claude-code-releases/"
  name "Claude Code"
  desc "Terminal-based AI coding assistant"
  homepage "https://www.anthropic.com/claude-code"

  livecheck do
    url "https://storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819/claude-code-releases/latest"
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
