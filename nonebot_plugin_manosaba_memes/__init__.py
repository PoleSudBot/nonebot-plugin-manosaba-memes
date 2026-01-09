from collections import defaultdict
import re

from nonebot import on_regex, require
from nonebot.internal.adapter import Bot, Event
from nonebot.plugin import PluginMetadata, inherit_supported_adapters

require("nonebot_plugin_alconna")

from nonebot_plugin_alconna import (
    Alconna,
    Args,
    Arparma,
    CommandMeta,
    UniMessage,
    on_alconna,
)

from .drawer import draw_anan, draw_trial
from .models import Option
from .utils import get_character, get_statement

__plugin_meta__ = PluginMetadata(
    name="魔裁 Memes",
    description="生成「魔法少女的魔法审判」的表情包",
    usage="""
🎨 安安说 (举牌生成)
• 安安说 [文本] [表情]
  └─ 让安安举起素描本
  表情：害羞/生气/病娇/无语/开心 (可选)
  💡 提示：内容中【中括号包裹】的文字会变成紫色
  示例：**安安说 吾辈命令你【去炒两个菜】 生气**

⚖️ 审判选项 (直接发送)
• 【类型】[文本]
  └─ 生成审判选项图 (支持多行/多选项)
  类型：疑问/反驳/伪证/赞同
  示例：
  `【伪证】我没有吃布丁`
  `【疑问】嘴角有残渣`

✨ 魔法选项
• 【魔法:[角色]】[文本]
  └─ 生成魔法技能选项
  示例：`【魔法:诺亚】液体操控`
  支持角色：诺亚/汉娜/雪莉/艾玛/希罗等

🔄 其他设置
• 切换角色 [艾玛/希罗]
  └─ 切换审判图右侧的立绘角色
""",
    type="application",
    homepage="https://github.com/zhaomaoniu/nonebot-plugin-manosaba-memes",
    supported_adapters=inherit_supported_adapters("nonebot_plugin_alconna"),
)

CHARACTER_MAP = defaultdict(lambda: get_character("艾玛"))


anan_says_handler = on_alconna(
    Alconna(
        "安安说",
        Args["text", str]["face", str, None],
        meta=CommandMeta(
            description="让安安说话的插件",
            usage="安安说 [文本] [表情]\n表情可选：害羞, 生气, 病娇, 无语, 开心",
            example="安安说 吾辈现在不想说话",
        ),
    ),
    aliases={"anan说", "anansays"},
    use_cmd_start=True,
)
trail_handler = on_regex(
    r"^【(疑问|反驳|伪证|赞同|魔法)(?:[:：]([^】]*))?】(.+)$", flags=re.MULTILINE
)
switch_character_handler = on_alconna(
    Alconna(
        "切换角色",
        Args["character", str],
        meta=CommandMeta(
            description="切换审判选择中的角色",
            usage="切换角色 [角色名]\n角色名可选：艾玛, 希罗",
            example="切换角色 希罗",
        ),
    ),
    use_cmd_start=True,
)


@anan_says_handler.handle()
async def handle_anan_says(result: Arparma):
    user_result = result["text"]
    face = result["face"]
    text = user_result.replace("\\n", "\n")
    image_bytes = draw_anan(text, face)
    await anan_says_handler.finish(
        UniMessage.image(raw=image_bytes, mimetype="image/png")
    )


@trail_handler.handle()
async def handle_trail(bot: Bot, event: Event):
    matches = re.findall(
        r"^【(疑问|反驳|伪证|赞同|魔法)(?:[:：]([^】]*))?】(.+)$",
        event.get_message().extract_plain_text(),
        flags=re.M,
    )

    options = []
    for statement_type, arg, text in matches:
        try:
            statement_enum = get_statement(statement_type, arg)
        except KeyError:
            if arg:
                await trail_handler.finish(
                    f"角色 {arg} 无效，请从以下选项中选择："
                    "梅露露, 诺亚, 汉娜, 奈叶香, 亚里沙, 米莉亚, 雪莉, 艾玛, 玛格, 安安, 可可, 希罗, 蕾雅"
                )
            else:
                await trail_handler.finish(
                    "魔法类型无效，请输入【魔法:角色】格式。可选的角色有："
                    "梅露露, 诺亚, 汉娜, 奈叶香, 亚里沙, 米莉亚, 雪莉, 艾玛, 玛格, 安安, 可可, 希罗, 蕾雅"
                )
        options.append(Option(statement_enum, text))

    try:
        image_bytes = draw_trial(CHARACTER_MAP[event.get_user_id()], options)
    except OverflowError:
        await trail_handler.finish("选项过多，请减少选项数量")
    await trail_handler.finish(
        await UniMessage.image(raw=image_bytes, mimetype="image/png").export(bot)
    )


@switch_character_handler.handle()
async def handle_switch_character(evemt: Event, result: Arparma):
    global CHARACTER_MAP
    character_name = result["character"]
    try:
        CHARACTER_MAP[evemt.get_user_id()] = get_character(character_name)
        await switch_character_handler.finish(f"已切换角色为 {character_name}")
    except KeyError:
        await switch_character_handler.finish(
            f"角色名 {character_name} 无效，请选择 艾玛 或 希罗"
        )
