#!/usr/bin/env python3
"""Generate the checked-in Xcode project using only Python's standard library."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
objects = {}
project_path = ROOT / 'Repcendo.xcodeproj/project.pbxproj'
# Keep device-signing choices made in Xcode when refreshing file references.
existing_objects = json.loads(subprocess.check_output(
    ['plutil', '-convert', 'json', '-o', '-', str(project_path)]
))['objects'] if project_path.exists() else {}


def uid(key):
    return hashlib.sha1(key.encode()).hexdigest()[:24].upper()


def add(key, body):
    ident = uid(key)
    objects[ident] = body
    return ident


def ref(key):
    return uid(key)


def quoted(value):
    return json.dumps(str(value), ensure_ascii=False)


def ids(values):
    return '(' + ', '.join(values) + (',' if values else '') + ')'


def files(paths, kind, phase):
    result = []
    for path in paths:
        relative = str(path.relative_to(ROOT))
        f = add('file:' + relative, f'isa = PBXFileReference; lastKnownFileType = {kind}; path = {quoted(relative)}; sourceTree = SOURCE_ROOT;')
        result.append(f)
        phase.append(add('build:' + relative, f'isa = PBXBuildFile; fileRef = {f};'))
    return result


sources, resources, tests = [], [], []
source_refs = files(sorted((ROOT / 'Repcendo').rglob('*.swift')), 'sourcecode.swift', sources)
resource_refs = files(sorted(p for p in (ROOT / 'Repcendo/Resources').glob('*') if p.is_file()), 'text', resources)
# Folder references preserve video/poster paths and keep these original assets separate from dataset text.
resource_refs += files([ROOT / 'Repcendo/Resources/ExerciseAnimations'], 'folder', resources)
test_refs = files(sorted((ROOT / 'RepcendoUITests').glob('*.swift')), 'sourcecode.swift', tests)
if (ROOT / 'Repcendo/Assets.xcassets').exists():
    f = add('assets', 'isa = PBXFileReference; lastKnownFileType = folder.assetcatalog; path = Repcendo/Assets.xcassets; sourceTree = SOURCE_ROOT;')
    resource_refs.append(f)
    resources.append(add('buildAssets', f'isa = PBXBuildFile; fileRef = {f};'))
app = add('appProduct', 'isa = PBXFileReference; explicitFileType = wrapper.application; path = Repcendo.app; sourceTree = BUILT_PRODUCTS_DIR;')
test = add('testProduct', 'isa = PBXFileReference; explicitFileType = wrapper.cfbundle; path = RepcendoUITests.xctest; sourceTree = BUILT_PRODUCTS_DIR;')
product_group = add('products', f'isa = PBXGroup; name = Products; sourceTree = "<group>"; children = {ids([app,test])};')
main_group = add('mainGroup', f'isa = PBXGroup; sourceTree = "<group>"; children = {ids(source_refs+resource_refs+test_refs+[product_group])};')
package = add('package', 'isa = XCLocalSwiftPackageReference; relativePath = Packages/RepcendoCore;')
package_product = add('packageProduct', f'isa = XCSwiftPackageProductDependency; package = {package}; productName = RepcendoCore;')
package_build = add('packageBuild', f'isa = PBXBuildFile; productRef = {package_product};')


def phase(key, isa, build_files):
    return add(key, f'isa = {isa}; buildActionMask = 2147483647; files = {ids(build_files)}; runOnlyForDeploymentPostprocessing = 0;')


app_phases = [phase('appSources', 'PBXSourcesBuildPhase', sources), phase('appResources', 'PBXResourcesBuildPhase', resources), phase('appFrameworks', 'PBXFrameworksBuildPhase', [package_build])]
test_phases = [phase('testSources', 'PBXSourcesBuildPhase', tests), phase('testResources', 'PBXResourcesBuildPhase', []), phase('testFrameworks', 'PBXFrameworksBuildPhase', [])]


def configs(key, settings):
    cs = []
    for name in ['Debug', 'Release']:
        all_settings = dict(settings)
        previous = existing_objects.get(uid(f'{key}{name}'), {}).get('buildSettings', {})
        for setting in ('DEVELOPMENT_TEAM', 'PRODUCT_BUNDLE_IDENTIFIER', 'CODE_SIGN_STYLE',
                        'CODE_SIGN_IDENTITY', 'PROVISIONING_PROFILE_SPECIFIER', 'CODE_SIGN_ENTITLEMENTS'):
            if setting in previous:
                all_settings[setting] = previous[setting]
        all_settings['SWIFT_OPTIMIZATION_LEVEL'] = '-Onone' if name == 'Debug' else '-O'
        if name == 'Debug':
            all_settings['SWIFT_ACTIVE_COMPILATION_CONDITIONS'] = 'DEBUG'
            all_settings['ENABLE_TESTABILITY'] = 'YES'
            all_settings['ONLY_ACTIVE_ARCH'] = 'YES'
        config = ' '.join(f'{k} = {quoted(v)};' for k, v in all_settings.items())
        cs.append(add(f'{key}{name}', f'isa = XCBuildConfiguration; name = {name}; buildSettings = {{{config}}};'))
    return add(f'{key}List', f'isa = XCConfigurationList; buildConfigurations = {ids(cs)}; defaultConfigurationIsVisible = 0; defaultConfigurationName = Release;')


base = dict(SDKROOT='iphoneos', IPHONEOS_DEPLOYMENT_TARGET='17.0', SWIFT_VERSION='5.0', CLANG_ENABLE_MODULES='YES', CODE_SIGN_STYLE='Automatic', TARGETED_DEVICE_FAMILY='1,2', SUPPORTED_PLATFORMS='iphoneos iphonesimulator')
project_config = configs('projectConfig', base)
app_config = configs('appConfig', dict(PRODUCT_BUNDLE_IDENTIFIER='com.repcendo.app', PRODUCT_NAME='$(TARGET_NAME)', GENERATE_INFOPLIST_FILE='YES', INFOPLIST_FILE='Repcendo/Info.plist', MARKETING_VERSION='0.1.0', CURRENT_PROJECT_VERSION='1', ASSETCATALOG_COMPILER_APPICON_NAME='AppIcon', INFOPLIST_KEY_UILaunchScreen_Generation='YES', INFOPLIST_KEY_CFBundleDisplayName='渐强', INFOPLIST_KEY_LSSupportsOpeningDocumentsInPlace='YES', INFOPLIST_KEY_UISupportedInterfaceOrientations='UIInterfaceOrientationPortrait UIInterfaceOrientationLandscapeLeft UIInterfaceOrientationLandscapeRight', INFOPLIST_KEY_UISupportedInterfaceOrientations_iPad='UIInterfaceOrientationPortrait UIInterfaceOrientationPortraitUpsideDown UIInterfaceOrientationLandscapeLeft UIInterfaceOrientationLandscapeRight', SUPPORTS_MACCATALYST='NO'))
test_config = configs('testConfig', dict(PRODUCT_BUNDLE_IDENTIFIER='com.repcendo.app.uitests', PRODUCT_NAME='$(TARGET_NAME)', GENERATE_INFOPLIST_FILE='YES', TEST_TARGET_NAME='Repcendo'))
proxy = add('appProxy', f'isa = PBXContainerItemProxy; containerPortal = {ref("project")}; proxyType = 1; remoteGlobalIDString = {ref("appTarget")}; remoteInfo = Repcendo;')
dependency = add('appDependency', f'isa = PBXTargetDependency; target = {ref("appTarget")}; targetProxy = {proxy};')
app_target = add('appTarget', f'isa = PBXNativeTarget; buildConfigurationList = {app_config}; buildPhases = {ids(app_phases)}; buildRules = (); dependencies = (); name = Repcendo; packageProductDependencies = {ids([package_product])}; productName = Repcendo; productReference = {app}; productType = "com.apple.product-type.application";')
test_target = add('testTarget', f'isa = PBXNativeTarget; buildConfigurationList = {test_config}; buildPhases = {ids(test_phases)}; buildRules = (); dependencies = {ids([dependency])}; name = RepcendoUITests; productName = RepcendoUITests; productReference = {test}; productType = "com.apple.product-type.bundle.ui-testing";')
project = add('project', f'isa = PBXProject; attributes = {{BuildIndependentTargetsInParallel = YES; LastUpgradeCheck = 1600; TargetAttributes = {{{app_target} = {{CreatedOnToolsVersion = 16.0;}}; {test_target} = {{CreatedOnToolsVersion = 16.0; TestTargetID = {app_target};}};}};}}; buildConfigurationList = {project_config}; compatibilityVersion = "Xcode 14.0"; developmentRegion = zh_Hans; hasScannedForEncodings = 0; knownRegions = (en, Base, zh_Hans); mainGroup = {main_group}; productRefGroup = {product_group}; packageReferences = {ids([package])}; projectDirPath = ""; projectRoot = ""; targets = {ids([app_target,test_target])};')
output = '// !$*UTF8*$!\n{\n archiveVersion = 1; classes = {}; objectVersion = 60;\n objects = {\n'
output += '\n'.join(f'  {k} = {{{v}}};' for k,v in objects.items())
output += f'\n }}; rootObject = {project};\n}}\n'
(ROOT / 'Repcendo.xcodeproj/project.pbxproj').write_text(output)
scheme = f'''<?xml version="1.0" encoding="UTF-8"?>
<Scheme LastUpgradeVersion="1600" version="1.7">
 <BuildAction parallelizeBuildables="YES" buildImplicitDependencies="YES"><BuildActionEntries>
 <BuildActionEntry buildForTesting="YES" buildForRunning="YES" buildForProfiling="YES" buildForArchiving="YES" buildForAnalyzing="YES"><BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="{app_target}" BuildableName="Repcendo.app" BlueprintName="Repcendo" ReferencedContainer="container:Repcendo.xcodeproj"/></BuildActionEntry>
 </BuildActionEntries></BuildAction>
 <TestAction buildConfiguration="Debug" selectedDebuggerIdentifier="Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier="Xcode.IDEFoundation.Launcher.LLDB" shouldUseLaunchSchemeArgsEnv="YES"><Testables><TestableReference skipped="NO"><BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="{test_target}" BuildableName="RepcendoUITests.xctest" BlueprintName="RepcendoUITests" ReferencedContainer="container:Repcendo.xcodeproj"/></TestableReference></Testables></TestAction>
 <LaunchAction buildConfiguration="Debug" selectedDebuggerIdentifier="Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier="Xcode.IDEFoundation.Launcher.LLDB" launchStyle="0" useCustomWorkingDirectory="NO" ignoresPersistentStateOnLaunch="NO" debugDocumentVersioning="YES" debugServiceExtension="internal" allowLocationSimulation="YES"><BuildableProductRunnable runnableDebuggingMode="0"><BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="{app_target}" BuildableName="Repcendo.app" BlueprintName="Repcendo" ReferencedContainer="container:Repcendo.xcodeproj"/></BuildableProductRunnable></LaunchAction>
 <ProfileAction buildConfiguration="Release" shouldUseLaunchSchemeArgsEnv="YES" savedToolIdentifier="" useCustomWorkingDirectory="NO" debugDocumentVersioning="YES"><BuildableProductRunnable runnableDebuggingMode="0"><BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="{app_target}" BuildableName="Repcendo.app" BlueprintName="Repcendo" ReferencedContainer="container:Repcendo.xcodeproj"/></BuildableProductRunnable></ProfileAction>
 <AnalyzeAction buildConfiguration="Debug"/><ArchiveAction buildConfiguration="Release" revealArchiveInOrganizer="YES"/>
</Scheme>
'''
(ROOT / 'Repcendo.xcodeproj/xcshareddata/xcschemes/Repcendo.xcscheme').write_text(scheme)
print('Generated Repcendo.xcodeproj')
