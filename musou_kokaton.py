import math
import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100
HEIGHT = 650
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird(pg.sprite.Sprite):
    delta = {
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }
    

    def __init__(self, num: int, xy: tuple[int, int]):
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        img = pg.transform.flip(img0, True, False)
        self.imgs = {
            (+1, 0): img,
            (+1, -1): pg.transform.rotozoom(img, 45, 0.9),
            (0, -1): pg.transform.rotozoom(img, 90, 0.9),
            (-1, -1): pg.transform.rotozoom(img0, -45, 0.9),
            (-1, 0): img0,
            (-1, +1): pg.transform.rotozoom(img0, 45, 0.9),
            (0, +1): pg.transform.rotozoom(img, -90, 0.9),
            (+1, +1): pg.transform.rotozoom(img, -45, 0.9),
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10

    def change_img(self, num: int, screen: pg.Surface):
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        sum_mv = [0, 0]

        if key_lst[pg.K_LSHIFT]:
            self.speed = 20
        else:
            self.speed = 10


        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed*sum_mv[0], self.speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        screen.blit(self.image, self.rect)


class Bomb(pg.sprite.Sprite):
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        super().__init__()
        rad = random.randint(10, 50)
        self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors)
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height//2
        self.speed = 6
        self.state = "active"  # EMPで無効化されたかの状態を記録

    def update(self):
        if self.state == "inactive":
            self.rect.move_ip(self.speed*self.vx*0.5, self.speed*self.vy*0.5)
        else:
            self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Beam(pg.sprite.Sprite):
    def __init__(self, bird: Bird):
        super().__init__()
        self.vx, self.vy = bird.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, 1.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10

    def update(self):
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Explosion(pg.sprite.Sprite):
    def __init__(self, obj: "Bomb|Enemy", life: int):
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        self.life -= 1
        self.image = self.imgs[self.life//10 % 2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]
    
    def __init__(self):
        super().__init__()
        self.image = pg.transform.rotozoom(random.choice(__class__.imgs), 0, 0.8)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vx, self.vy = 0, +6
        self.bound = random.randint(50, HEIGHT//2)
        self.state = "down"
        self.interval = random.randint(50, 300)

    def update(self):
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.move_ip(self.vx, self.vy)


class Shield(pg.sprite.Sprite):
    """
    こうかとんの前に防御壁を出現させ、着弾を防ぐ
    発動時間:400フレーム
    発動条件:「s」キー押下、スコアが50以上、防御壁が他に存在しない
    消費スコア:50
    """
    def __init__(self, bird: Bird, life: int):
        super().__init__()
        self.life = life
        width = 20
        height = bird.rect.height * 2
        self.image = pg.Surface((width,height))  # 空のSurfaceを生成
        pg.draw.rect(self.image, (0,0,255),(0,0,width,height))  # 防御壁を生成
        vx, vy = bird.dire  # こうかとんの向きを取得する
        angle = math.degrees(math.atan2(-vy,vx))  # 角度を求める
        self.image = pg.transform.rotozoom(self.image, angle, 1.0)  # 向きに合わせて防御壁を回転させる
        self.rect = self.image.get_rect()
        self.rect.centerx = bird.rect.centerx + bird.rect.width * vx  # こうかとんの中心からこうかとん1体分ずらした位置に配置
        self.rect.centery = bird.rect.centery + bird.rect.height * vy
        self.image.set_colorkey((0,0,0))

    def update(self):
        self.life -= 1
        if self.life < 0:  # ライフが0未満になったら消滅
            self.kill()


class Score:
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)


class EMP(pg.sprite.Sprite):
    """電磁パルス：敵機・爆弾を無効化"""
    def __init__(self, emys: pg.sprite.Group, bombs: pg.sprite.Group, screen: pg.Surface):
        super().__init__()
        # 半透明の黄色矩形
        self.image = pg.Surface((WIDTH, HEIGHT))
        self.image.fill((255, 255, 0))
        self.image.set_alpha(128)
        self.rect = self.image.get_rect()
        self.life = 3  # 約0.05秒 (3フレーム)
        # 敵機と爆弾を無効化
        for emy in emys:
            emy.interval = math.inf
            emy.image = pg.transform.laplacian(emy.image)
        for bomb in bombs:
            bomb.speed *= 0.5
            bomb.state = "inactive"

    def update(self):
        self.life -= 1
        if self.life < 0:
            self.kill()
class Gravity(pg.sprite.Sprite):
    """
    画面全体を覆う「重力場」クラス
    ・半透明の黒い矩形を描画
    ・life(発動時間)のあいだ有効
    ・範囲内の爆弾/敵機に衝突扱いを起こし，爆発エフェクト生成のうえ削除
    """
    def __init__(self, life: int = 400):
        super().__init__()
        # 画面全体サイズのSurfaceを作成（半透明の黒）
        self.image = pg.Surface((WIDTH, HEIGHT))
        self.image.fill((0, 0, 0))
        self.image.set_alpha(140) 
        self.rect = self.image.get_rect(topleft=(0, 0))
        self.life = life  # 発動時間（フレーム）

    def update(self):
        # スライドの実装例に合わせて life を毎フレーム減算し，0でkill
        self.life -= 1
        if self.life <= 0:
            self.kill()


def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    score = Score()

    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    emps = pg.sprite.Group()  # EMPグループ
    gravs = pg.sprite.Group()  # 重力場グループ（実装例にあるとおり追加）
    shields = pg.sprite.Group()

    tmr = 0
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.add(Beam(bird))
            # EMP発動処理
            if event.type == pg.KEYDOWN and event.key == pg.K_e:
                    score.value -= 20
                    emps.add(EMP(emys, bombs, screen))
            # === 重力場の発動（Enterキー & スコアが200以上 & 未発動時） ===
            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                if score.value >= 200 and len(gravs) == 0:
                    gravs.add(Gravity(life=400))  # 発動時間：400フレーム
                    score.value -= 200                 # 消費スコア：200
            if event.type == pg.KEYDOWN and event.key == pg.K_s:
                if score.value >= 50 and len(shields) == 0:
                    shields.add(Shield(bird, 400))
                    score.value -= 50

        screen.blit(bg_img, [0, 0])
        if tmr % 200 == 0:
            emys.add(Enemy())

        for emy in emys:
            if emy.state == "stop" and tmr % emy.interval == 0:
                bombs.add(Bomb(emy, bird))

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            exps.add(Explosion(emy, 100))
            score.value += 10
            bird.change_img(6, screen)

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
            exps.add(Explosion(bomb, 50))
            score.value += 1

        for bomb in pg.sprite.spritecollide(bird, bombs, True):
            if bomb.state != "inactive":  # EMPで無効化された爆弾は爆発せず消滅
                bird.change_img(8, screen)
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return
            
        


        for g in gravs:
            for bomb in pg.sprite.spritecollide(g, bombs, True):
                exps.add(Explosion(bomb, 50))
            for emy in pg.sprite.spritecollide(g, emys, True):
                exps.add(Explosion(emy, 100))

        for bomb in pg.sprite.spritecollide(bird, bombs, True):  # こうかとんと衝突した爆弾リスト
            bird.change_img(8, screen)  # こうかとん悲しみエフェクト
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return
        
        for bomb in pg.sprite.groupcollide(bombs,shields,True,False).keys():  # 防御壁と衝突した爆弾リスト
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト

        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)

        # 重力場は半透明のオーバーレイなので最後に描画
        gravs.update()
        gravs.draw(screen)

        exps.update()
        exps.draw(screen)
        score.update(screen)
        shields.update()
        shields.draw(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
