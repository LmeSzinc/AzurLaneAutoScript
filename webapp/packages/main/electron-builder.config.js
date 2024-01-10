module.exports = {
  directories: {
    output: '../../release',
    buildResources: 'build',
  },
  files: ['dist'],
  extraMetadata: {
    version: process.env.npm_package_version,
  },

  /**
   *  app 基础信息
   */
  appId: 'com.azur-lane-auto-script.webapp',
  productName: 'AzurLaneAutoScript',
  copyright: 'Copyright © 2021 - ALAS | All Right Reserved.',

  /**
   * 配置 notarize dmg
   * 在 `.env` 里添加两个环境变量
   *
   * APPLE_ID=你的apple id
   * APPLE_ID_PASSWORD= app-specific 密码 可以在 appleid.apple.com 创建
   *
   */
  // afterSign:
  //   process.env.NOTARIZE === 'false'
  //     ? () => {
  //         console.log('Skip notarize...');
  //       }
  //     : 'electron-builder-notarize',

  /**
   * win 配置项
   */
  // win: {
  //   artifactName: '${name}_setup_${version}.${ext}',
  //   target: ['nsis'],
  // },
  // nsis: {
  //   oneClick: false,
  //   perMachine: true,
  //   allowToChangeInstallationDirectory: true,
  //   license: 'build/license.txt',
  // },

  /**
   * mac 配置项
   */
  // mac: {
  // category: 'public.app-category.developer-tools',
  // target: ['dmg'],
  // artifactName: '${name}_setup_${version}.${ext}',
  // hardenedRuntime: true,
  // gatekeeperAssess: false,
  // darkModeSupport: true,
  // entitlements: 'build/entitlements.mac.plist',
  // entitlementsInherit: 'build/entitlements.mac.plist',
  // },
  // dmg: {
  //   icon: 'build/volume.icns',
  //   background: 'build/background.png',
  //   title: '${productName}',
  //   iconSize: 80,
  //   window: {
  //     height: 422,
  //     width: 600,
  //   },
  //   contents: [
  //     {
  //       type: 'file',
  //       x: 144,
  //       y: 199,
  //     },
  //     {
  //       type: 'link',
  //       path: '/Applications',
  //       x: 451,
  //       y: 199,
  //     },
  //   ],
  // },
  // mas: {
  //   hardenedRuntime: false,
  //   darkModeSupport: true,
  //   provisioningProfile: 'build/embedded.provisionprofile',
  //   category: 'public.app-category.productivity',
  //   entitlements: 'build/entitlements.mas.plist',
  //   entitlementsInherit: 'build/entitlements.mas.inherit.plist',
  //   asarUnpack: [],
  // },

  /**
   * linux 配置项
   */
  linux: {
    // artifactName: '${name}_setup_${version}.${ext}',
    // icon: 'build/icon.png',
    // synopsis: 'azur lane auto script',
    // category: 'Development',
    target: 'deb',
  },

  /**
   * Publish 配置
   */
  // publish: ['github'],

  /**
   * 构建配置项
   */
  // compression: 'maximum', // 压缩比例
  // // npmRebuild: true,
  // // asar: {
  // //   smartUnpack: true,
  // // },
};
