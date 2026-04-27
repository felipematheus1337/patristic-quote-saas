package bff_patristic.v1;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;

@SpringBootApplication
@EnableFeignClients
public class V1Application {

	public static void main(String[] args) {
		SpringApplication.run(V1Application.class, args);
	}

}
