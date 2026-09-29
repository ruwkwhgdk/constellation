$ErrorActionPreference = 'Stop'
$kitRoot = Join-Path $PSScriptRoot '../Production/v001'
$manifest = Get-Content -LiteralPath (Join-Path $kitRoot 'reports/asset_manifest.json') -Raw | ConvertFrom-Json
$approved = Test-Path (Join-Path $kitRoot 'reports/appearance_approval.json')
$reviewStatus = if ($approved) { '외형 전체 채택 완료 · 텍스처/재질 보완 및 원화 장면 재현 진행 중' } else { '기술 검사와 외형 승인은 별도입니다. 신규 애셋은 사용자 외형 검토 대기입니다.' }
$cards = foreach ($asset in ($manifest.assets | Sort-Object id,name)) {
    $name = [System.Net.WebUtility]::HtmlEncode($asset.name)
    $dimensions = ($asset.dimensions_cm | ForEach-Object { '{0:0.##}' -f $_ }) -join ' × '
    $route = if ($asset.route -like '*tripo*') { 'Tripo 원본 보정' } else { 'Blender 직접 제작' }
    @"
<article><a href="renders/$name.png"><img loading="lazy" src="renders/$name.png" alt="$name"></a><div class="body"><b>$($asset.id) · $name</b><p>$route · $($asset.triangles) tris / $($asset.budget)</p><p>$dimensions cm · 충돌 $($asset.collision_hulls)개</p></div></article>
"@
}
$html = @"
<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>계단실 모듈러 애셋 검토 v001</title>
<style>body{margin:0;background:#171b20;color:#e7edf4;font:15px/1.6 system-ui,sans-serif}header,main{max-width:1500px;margin:auto;padding:30px}h1{margin:0;font-size:28px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px}article{background:#242c35;border:1px solid #3a4654;border-radius:12px;overflow:hidden}img{display:block;width:100%;aspect-ratio:1;object-fit:contain}.body{padding:14px}.body b{font-size:13px;overflow-wrap:anywhere}p{margin:6px 0;color:#bccbda}a{color:#8eceff}.status{color:#ffda89}code{overflow-wrap:anywhere}details{margin-top:14px}summary{cursor:pointer}</style>
<header><h1>계단실 모듈러 애셋 · v001</h1><p>채택 번호 01–22 · 길이·방향 파생형 포함 31개 메시</p><p class="status">$reviewStatus</p><p>타일·벽·계단·난간은 Blender 직접 제작, 문짝·형광등은 Tripo 결과를 보정했습니다. 이미지를 누르면 원본 렌더를 볼 수 있습니다.</p><p><a href="stairwell_kit_review_v001.blend">Blender 검토 파일</a> · <a href="reports/asset_manifest.json">전체 명세</a> · <a href="reports/geometry_verification.json">기하 검사</a> · <a href="reports/unreal_import_verification.json">Unreal 임포트 검사</a> · <a href="reports/assembly_verification.json">조립 검사</a></p><details><summary>검토 안내와 한계</summary><p>전체 외형은 채택되었습니다. 후속 피드백은 번호와 파생형 이름으로 지정할 수 있습니다.</p><p>새 규격형 애셋의 표면은 기본 재질 단계입니다. 원화 수준의 오염·녹·사용 흔적은 후속 보완 대상입니다. 형광등에는 원본 경계 엣지가 남아 있어 방수형 메시로 분류하지 않습니다.</p><p>문 개폐 입력·런타임 애니메이션과 캐릭터 PIE 이동 검사는 별도입니다.</p><p>Unreal: <code>/Game/Environment/StairwellModular/ReviewKit/Maps/L_Stairwell_KitReview</code></p><p><a href="renders/SM_SW_15_LightFixture_underside.png">형광등 하부 렌더</a> · <a href="../../Workflow/CURRENT.md">원화 장면 작업</a></p></details></header><main class="grid">$($cards -join "`n")</main></html>
"@
[System.IO.File]::WriteAllText((Join-Path $kitRoot 'review.html'), $html, [System.Text.UTF8Encoding]::new($false))
Write-Output "REVIEW_INDEX_CREATED $($manifest.assets.Count)"
